"""Historical success weighting for the matching engine."""

from sqlalchemy import case, func, select
from sqlmodel import Session

from app.db.models import ApplicationEvidenceLink

# Weights per Implementation Guide section 12.2.
INTERVIEW_ALPHA = 0.1
OFFER_BETA = 0.2


class HistoricalWeightingService:
    """Computes historical success weights for knowledge items.

    weight = alpha * interview_rate + beta * offer_rate, where an offer
    counts toward both rates. Items without history weigh 0.0.
    """

    def __init__(self, session: Session) -> None:
        self.session = session

    def calculate_weight(self, item_id: str) -> float:
        """Weight for one item (delegates to the repository formula)."""
        from app.repositories.application import ApplicationRepository

        return ApplicationRepository(self.session).get_success_weight(item_id)

    def calculate_weights_bulk(self, item_ids: list[str]) -> dict[str, float]:
        """Weights for many items via a single aggregated query."""
        if not item_ids:
            return {}

        interview_or_offer = func.sum(
            case(
                (
                    ApplicationEvidenceLink.result.in_(["interview", "offer"]),  # type: ignore[attr-defined]
                    1,
                ),
                else_=0,
            )
        )
        offers = func.sum(
            case(
                (ApplicationEvidenceLink.result == "offer", 1),
                else_=0,
            )
        )
        total = func.count(ApplicationEvidenceLink.result)

        stmt = (
            select(
                ApplicationEvidenceLink.knowledge_item_id,
                interview_or_offer,
                offers,
                total,
            )
            .where(
                ApplicationEvidenceLink.knowledge_item_id.in_(item_ids),  # type: ignore[attr-defined]
                ApplicationEvidenceLink.result.is_not(None),  # type: ignore[attr-defined]
            )
            .group_by(ApplicationEvidenceLink.knowledge_item_id)
        )

        weights: dict[str, float] = {}
        for item_id, interviews, offer_count, recorded in self.session.execute(stmt):
            weights[item_id] = (
                INTERVIEW_ALPHA * (interviews / recorded)
                + OFFER_BETA * (offer_count / recorded)
            )
        return weights

    def update_weights(self, item_ids: list[str]) -> dict[str, float]:
        """Recompute weights after application results change.

        Weights are derived live from application_evidence on every
        ranking pass, so 'updating' simply recomputes and returns them.
        """
        return self.calculate_weights_bulk(item_ids)
