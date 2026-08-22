"""Validation engine: completeness, keywords, traceability, and length."""

from typing import Optional

from pydantic import BaseModel


class ValidationIssue(BaseModel):
    """One validation finding."""

    rule: str
    severity: str  # "error" | "warning"
    message: str
    field: Optional[str] = None


class ValidationResult(BaseModel):
    """Aggregated outcome of validating one built document."""

    valid: bool
    errors: list[ValidationIssue]
    warnings: list[ValidationIssue]
    score: float  # 0.0 - 1.0


DOC_TYPES = {"resume", "soq", "duty"}

RESUME_MAX_WORDS = 1000
SOQ_MIN_WORDS = 50
SOQ_DEFAULT_MAX_WORDS = 250
DUTY_MAX_WORDS_PER_DUTY = 200
MIN_SKILLS = 3

ERROR_PENALTY = 0.25
WARNING_PENALTY = 0.05


def count_words(text: str) -> int:
    return len(text.split())


class ValidationService:
    """Runs the four rule families against a built document."""

    def validate(
        self,
        document,
        doc_type: str = "resume",
        keywords: Optional[list[str]] = None,
        soq_max_words: int = SOQ_DEFAULT_MAX_WORDS,
    ) -> ValidationResult:
        """Validate deterministically; identical input yields identical output."""
        doc_type = doc_type.lower()
        if doc_type not in DOC_TYPES:
            raise ValueError(f"Unknown doc_type: {doc_type}")

        errors: list[ValidationIssue] = []
        warnings: list[ValidationIssue] = []

        self._check_completeness(document, doc_type, soq_max_words, errors)
        self._check_keyword_coverage(document, keywords or [], warnings)
        self._check_evidence_traceability(document, warnings)
        self._check_length(document, doc_type, soq_max_words, errors, warnings)

        score = 1.0
        score -= ERROR_PENALTY * len(errors)
        score -= WARNING_PENALTY * len(warnings)
        score = max(0.0, min(score, 1.0))

        return ValidationResult(
            valid=not errors,
            errors=errors,
            warnings=warnings,
            score=round(score, 2),
        )

    # --- completeness ---

    def _check_completeness(self, document, doc_type, soq_max_words, errors) -> None:
        if doc_type == "resume":
            self._completeness_resume(document, errors)
        elif doc_type == "soq":
            self._completeness_soq(document, soq_max_words, errors)
        else:
            self._completeness_duty(document, errors)

    def _completeness_resume(self, document, errors) -> None:
        profile = next(
            (s for s in document.sections if s.section_type == "profile"), None
        )
        contact_text = " ".join(profile.profile_lines) if profile else ""
        has_contact = "@" in contact_text or _digit_count(contact_text) >= 7
        if not contact_text.strip() or not has_contact:
            errors.append(
                ValidationIssue(
                    rule="completeness",
                    severity="error",
                    message="Resume is missing contact information",
                    field="profile",
                )
            )

        experience = next(
            (s for s in document.sections if s.section_type == "experience"), None
        )
        bullet_count = (
            sum(len(g.bullets) for g in experience.groups) if experience else 0
        )
        if bullet_count < 1:
            errors.append(
                ValidationIssue(
                    rule="completeness",
                    severity="error",
                    message="Resume needs at least one experience bullet",
                    field="experience",
                )
            )

        skills = next(
            (s for s in document.sections if s.section_type == "skills"), None
        )
        skill_count = len(skills.lines) if skills else 0
        if skill_count < MIN_SKILLS:
            errors.append(
                ValidationIssue(
                    rule="completeness",
                    severity="error",
                    message=f"Resume lists {skill_count} skill(s); "
                    f"at least {MIN_SKILLS} required",
                    field="skills",
                )
            )

    def _completeness_soq(self, document, soq_max_words, errors) -> None:
        question = next(
            (s for s in document.sections if s.section_type == "soq_question"),
            None,
        )
        if question is None or not question.profile_lines:
            errors.append(
                ValidationIssue(
                    rule="completeness",
                    severity="error",
                    message="SOQ response is missing the question section",
                    field="soq_question",
                )
            )

        response = next(
            (s for s in document.sections if s.section_type == "soq_response"),
            None,
        )
        answer_words = count_words(" ".join(response.lines)) if response else 0
        if answer_words < SOQ_MIN_WORDS:
            errors.append(
                ValidationIssue(
                    rule="completeness",
                    severity="error",
                    message=f"SOQ answer is {answer_words} words; "
                    f"minimum {SOQ_MIN_WORDS} required",
                    field="soq_response",
                )
            )
        elif answer_words > soq_max_words:
            errors.append(
                ValidationIssue(
                    rule="length",
                    severity="error",
                    message=f"SOQ answer exceeds {soq_max_words}-word limit",
                    field="soq_response",
                )
            )

    def _completeness_duty(self, document, errors) -> None:
        section = next(
            (s for s in document.sections if s.section_type == "duty_response"),
            None,
        )
        if section is None or not section.groups:
            errors.append(
                ValidationIssue(
                    rule="completeness",
                    severity="error",
                    message="No duty responses were assembled",
                    field="duty_response",
                )
            )

    # --- keyword coverage ---

    def _check_keyword_coverage(self, document, keywords, warnings) -> None:
        if not keywords:
            return
        full_text = self._collect_text(document).lower()
        missing = [k for k in keywords if k.lower() not in full_text]
        coverage = round(
            (len(keywords) - len(missing)) / len(keywords) * 100
        )
        if missing:
            warnings.append(
                ValidationIssue(
                    rule="keyword_coverage",
                    severity="warning",
                    message=f"Keyword coverage {coverage}% — "
                    f"missing: {', '.join(missing)}",
                    field=None,
                )
            )

    # --- evidence traceability ---

    def _check_evidence_traceability(self, document, warnings) -> None:
        orphan_groups = [
            group.title
            for section in document.sections
            for group in section.groups
            if group.evidence_id == "_unlinked"
        ]
        if orphan_groups:
            warnings.append(
                ValidationIssue(
                    rule="evidence_traceability",
                    severity="warning",
                    message=f"{len(orphan_groups)} content block(s) have no "
                    f"evidence link",
                    field=None,
                )
            )
        elif self._has_content(document) and not document.traceability:
            warnings.append(
                ValidationIssue(
                    rule="evidence_traceability",
                    severity="warning",
                    message="Content has no evidence links",
                    field=None,
                )
            )

    # --- length ---

    def _check_length(self, document, doc_type, soq_max_words, errors, warnings) -> None:
        if doc_type == "resume":
            word_count = count_words(self._collect_text(document))
            if word_count > RESUME_MAX_WORDS:
                errors.append(
                    ValidationIssue(
                        rule="length",
                        severity="error",
                        message=f"Resume is {word_count} words; "
                        f"maximum {RESUME_MAX_WORDS}",
                        field=None,
                    )
                )
        elif doc_type == "duty":
            for section in document.sections:
                for group in section.groups:
                    for bullet in group.bullets:
                        if count_words(bullet) > DUTY_MAX_WORDS_PER_DUTY:
                            warnings.append(
                                ValidationIssue(
                                    rule="length",
                                    severity="warning",
                                    message=f"Duty '{group.title[:40]}…' "
                                    f"exceeds {DUTY_MAX_WORDS_PER_DUTY} words",
                                    field=None,
                                )
                            )

    # --- helpers ---

    @staticmethod
    def _collect_text(document) -> str:
        parts: list[str] = []
        for section in document.sections:
            parts.extend(section.profile_lines)
            parts.extend(line for group in section.groups for line in group.bullets)
            parts.extend(section.lines)
        return " ".join(parts)

    @staticmethod
    def _has_content(document) -> bool:
        return any(
            section.groups or section.lines or section.profile_lines
            for section in document.sections
        )


def _digit_count(text: str) -> int:
    return sum(1 for ch in text if ch.isdigit())
