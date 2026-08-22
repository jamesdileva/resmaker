"""Application repository with evidence usage tracking and success weights."""

from typing import Optional

from sqlalchemy import text
from sqlmodel import select

from app.db.models import Application, ApplicationEvidenceLink
from app.repositories.base import BaseRepository

INTERVIEW_WEIGHT_ALPHA = 0.1
OFFER_WEIGHT_BETA = 0.2


class ApplicationRepository(BaseRepository[Application]):
    """CRUD for applications plus historical success weighting."""

    model = Application

    def create(self, application: Application) -> Application:
        return self.add(application)

    def get(self, application_id: str) -> Optional[Application]:
        return self.session.get(Application, application_id)

    def update_result(
        self, application_id: str, status: str
    ) -> Optional[Application]:
        """Set an application's outcome status."""
        application = self.get(application_id)
        if application is None:
            return None
        application.status = status
        self.session.add(application)
        self.session.commit()
        self.session.refresh(application)
        return application

    def record_evidence_usage(
        self,
        application_id: str,
        item_id: str,
        used_in_resume: bool = False,
        used_in_soq: bool = False,
        used_in_duty: bool = False,
        result: Optional[str] = None,
    ) -> None:
        """Insert or update the usage link between an application and an item."""
        existing = self.session.exec(
            select(ApplicationEvidenceLink)
            .where(ApplicationEvidenceLink.application_id == application_id)
            .where(ApplicationEvidenceLink.knowledge_item_id == item_id)
        ).first()
        if existing is not None:
            existing.used_in_resume = used_in_resume
            existing.used_in_soq = used_in_soq
            existing.used_in_duty = used_in_duty
            existing.result = result
        else:
            existing = ApplicationEvidenceLink(
                application_id=application_id,
                knowledge_item_id=item_id,
                used_in_resume=used_in_resume,
                used_in_soq=used_in_soq,
                used_in_duty=used_in_duty,
                result=result,
            )
        self.session.add(existing)
        self.session.commit()

    def get_success_weight(self, item_id: str) -> float:
        """Historical weighting score in [0.0, 0.3].

        weight = alpha * interview_rate + beta * offer_rate, where an
        offer counts as both. Items without usage history score 0.0.
        """
        sql = text(
            "SELECT result FROM application_evidence "
            "WHERE knowledge_item_id = :item_id AND result IS NOT NULL"
        )
        rows = self.session.execute(sql, {"item_id": item_id}).all()
        if not rows:
            return 0.0
        results = [row[0] for row in rows]
        total = len(results)
        interviews = sum(1 for r in results if r in ("interview", "offer"))
        offers = sum(1 for r in results if r == "offer")
        return (
            INTERVIEW_WEIGHT_ALPHA * interviews / total
            + OFFER_WEIGHT_BETA * offers / total
        )
