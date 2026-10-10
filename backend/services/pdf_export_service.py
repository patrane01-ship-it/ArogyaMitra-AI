"""
ArogyaMitra AI - PDF Export Service
Generates clean, professional Doctor-Prep reports in PDF format using ReportLab.
Per FEATURES.md §3 (Feature 5) and TECH_STACK.md §1.
"""

import io
from typing import List, Dict, Any, Optional
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from backend.core.logger import logger
from backend.exceptions.arogya_errors import ArogyaError


class PDFExportService:
    """Generates structured PDF reports using ReportLab."""

    @staticmethod
    def generate_report_pdf(
        report_content: str,
        user_id: str = "local_user",
        clinical_params: Optional[List[Dict[str, Any]]] = None,
        reminders: Optional[List[Dict[str, Any]]] = None,
    ) -> bytes:
        """
        Render doctor-prep report into a high quality PDF byte stream.
        """
        try:
            buffer = io.BytesIO()
            doc = SimpleDocTemplate(
                buffer,
                pagesize=letter,
                rightMargin=40,
                leftMargin=40,
                topMargin=40,
                bottomMargin=40,
            )

            story = []
            styles = getSampleStyleSheet()

            # Custom styles
            title_style = ParagraphStyle(
                "DocTitle",
                parent=styles["Heading1"],
                fontName="Helvetica-Bold",
                fontSize=20,
                leading=24,
                textColor=colors.HexColor("#1A6B5A"),
                spaceAfter=6,
            )

            subtitle_style = ParagraphStyle(
                "DocSubtitle",
                parent=styles["Normal"],
                fontName="Helvetica",
                fontSize=10,
                leading=14,
                textColor=colors.HexColor("#718096"),
                spaceAfter=12,
            )

            section_heading = ParagraphStyle(
                "SectionHeading",
                parent=styles["Heading2"],
                fontName="Helvetica-Bold",
                fontSize=13,
                leading=16,
                textColor=colors.HexColor("#1A6B5A"),
                spaceBefore=14,
                spaceAfter=6,
            )

            body_style = ParagraphStyle(
                "BodyTextCustom",
                parent=styles["Normal"],
                fontName="Helvetica",
                fontSize=9.5,
                leading=14,
                textColor=colors.HexColor("#2D3748"),
                spaceAfter=6,
            )

            disclaimer_style = ParagraphStyle(
                "Disclaimer",
                parent=styles["Italic"],
                fontName="Helvetica-Oblique",
                fontSize=8,
                leading=11,
                textColor=colors.HexColor("#A0AEC0"),
                spaceBefore=16,
            )

            # Header
            story.append(Paragraph("ArogyaMitra AI — Doctor-Prep Health Summary", title_style))
            story.append(
                Paragraph(
                    f"Patient ID: <b>{user_id}</b> | Generated for clinical consultation",
                    subtitle_style,
                )
            )
            story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#4ECBA0"), spaceAfter=12))

            # Main AI Summary Content
            story.append(Paragraph("Clinical Summary & Doctor Guidance", section_heading))
            # Format markdown paragraphs
            paragraphs = report_content.split("\n\n")
            for p in paragraphs:
                clean_p = p.strip()
                if not clean_p:
                    continue
                # Bold markdown conversion
                clean_p = clean_p.replace("**", "<b>", 1)
                while "**" in clean_p:
                    clean_p = clean_p.replace("**", "</b>", 1)
                    clean_p = clean_p.replace("**", "<b>", 1)
                story.append(Paragraph(clean_p.replace("\n", "<br/>"), body_style))

            # Parameters Table (if available)
            if clinical_params:
                story.append(Spacer(1, 10))
                story.append(Paragraph("Recent Clinical Parameters", section_heading))
                table_data = [["Parameter", "Value", "Unit", "Ref Range", "Status"]]
                
                for p in clinical_params:
                    status = p.get("status", "NORMAL")
                    ref_min = p.get("reference_range_min") or p.get("ref_min", "")
                    ref_max = p.get("reference_range_max") or p.get("ref_max", "")
                    ref_str = f"{ref_min} - {ref_max}" if ref_min or ref_max else "N/A"

                    table_data.append([
                        p.get("param_name") or p.get("name", ""),
                        str(p.get("value", "")),
                        p.get("unit", ""),
                        ref_str,
                        status,
                    ])

                t = Table(table_data, colWidths=[160, 70, 70, 110, 80])
                t.setStyle(
                    TableStyle([
                        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1A6B5A")),
                        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                        ("FONTSIZE", (0, 0), (-1, 0), 9),
                        ("BOTTOMPADDING", (0, 0), (-1, 0), 6),
                        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
                        ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
                        ("FONTSIZE", (0, 1), (-1, -1), 8.5),
                        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F7FAFC")]),
                    ])
                )
                story.append(t)

            # Active Reminders / Medications (if available)
            if reminders:
                story.append(Spacer(1, 10))
                story.append(Paragraph("Active Medications & Schedules", section_heading))
                rem_data = [["Type", "Medication / Action", "Due Date / Recurrence"]]
                for r in reminders:
                    rem_data.append([
                        r.get("reminder_type", "MEDICATION"),
                        r.get("title", ""),
                        f"{str(r.get('due_date', ''))[:10]} ({r.get('recurrence', 'NONE')})",
                    ])
                t_rem = Table(rem_data, colWidths=[100, 250, 140])
                t_rem.setStyle(
                    TableStyle([
                        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2C7A7B")),
                        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                        ("FONTSIZE", (0, 0), (-1, 0), 9),
                        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
                        ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
                        ("FONTSIZE", (0, 1), (-1, -1), 8.5),
                    ])
                )
                story.append(t_rem)

            # Mandatory Medical Disclaimer
            story.append(Spacer(1, 16))
            story.append(
                Paragraph(
                    "NOTICE: This document is an automated clinical summary prepared by ArogyaMitra AI "
                    "for patient-doctor communication. It is NOT a medical diagnosis or treatment prescription. "
                    "All clinical findings and therapies must be evaluated and authorized by a licensed healthcare provider.",
                    disclaimer_style,
                )
            )

            doc.build(story)
            pdf_bytes = buffer.getvalue()
            buffer.close()

            if len(pdf_bytes) == 0:
                raise ArogyaError("PDF export generated zero bytes", status_code=500)

            return pdf_bytes

        except Exception as e:
            logger.error(f"[PDFExportService] Failed to generate PDF: {e}")
            raise ArogyaError(f"PDF generation failed: {e}", status_code=500)
