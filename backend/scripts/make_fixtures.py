"""Generate DOCX test fixtures for the parser test suite."""

from pathlib import Path

from docx import Document

FIXTURES_DIR = Path(__file__).resolve().parent.parent / "tests" / "fixtures"


def make_sample_resume(path: Path) -> None:
    document = Document()

    document.add_heading("John Doe", level=1)
    document.add_paragraph(
        "Customer service professional with 5+ years of experience."
    )

    document.add_heading("Sales Associate - Boost Mobile (2019-2022)", level=2)
    bullets_1 = [
        "Handled confidential customer records and account verification daily",
        "Resolved customer complaints, maintaining a 95% satisfaction rating",
        "Trained 4 new employees on point-of-sale and inventory systems",
    ]
    for text in bullets_1:
        document.add_paragraph(text, style="List Bullet")

    nested = document.add_paragraph(
        "Processed payments and reconciled cash drawers", style="List Bullet 2"
    )
    assert nested.style.name == "List Bullet 2"

    document.add_heading("Data Entry Clerk - County Office (2017-2019)", level=2)
    bullets_2 = [
        "Performed data analysis on weekly intake reports using Excel",
        "Maintained filing systems for over 500 sensitive documents",
    ]
    for text in bullets_2:
        document.add_paragraph(text, style="List Bullet")

    document.add_paragraph("Proficient in Excel, SQL dashboards, and CRM tools.")
    document.save(str(path))


def make_sample_soq(path: Path) -> None:
    document = Document()

    document.add_heading("Statement of Qualifications", level=1)
    document.add_paragraph("Applicant: John Doe")

    document.add_heading(
        "Question 1: Describe your experience handling confidential information",
        level=2,
    )
    document.add_paragraph(
        "Throughout my five years at Boost Mobile I managed confidential "
        "customer records, verifying identities and protecting private data "
        "in compliance with company privacy policies."
    )

    document.add_heading(
        "Question 2: Describe your analytical experience",
        level=2,
    )
    document.add_paragraph(
        "As a data entry clerk I performed weekly analysis of intake reports, "
        "built Excel dashboards, and presented summary findings to management."
    )

    document.save(str(path))


def main() -> None:
    FIXTURES_DIR.mkdir(parents=True, exist_ok=True)
    resume_path = FIXTURES_DIR / "sample_resume.docx"
    soq_path = FIXTURES_DIR / "sample_soq.docx"
    make_sample_resume(resume_path)
    make_sample_soq(soq_path)
    print(f"Created {resume_path}")
    print(f"Created {soq_path}")


if __name__ == "__main__":
    main()
