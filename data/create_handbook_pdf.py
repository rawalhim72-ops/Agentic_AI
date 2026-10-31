"""
Generates the synthetic Student Policy Handbook PDF using ReportLab.
Contains official institutional demonstration policies on fees, late payments,
portal failures, scholarships, course changes, academic support, and grievances.
"""

from pathlib import Path
import sys
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from config.settings import settings


def generate_handbook_pdf():
    pdf_path = settings.HANDBOOK_PDF_PATH
    settings.DATA_DIR.mkdir(parents=True, exist_ok=True)

    doc = SimpleDocTemplate(
        str(pdf_path),
        pagesize=letter,
        rightMargin=40,
        leftMargin=40,
        topMargin=40,
        bottomMargin=40,
    )

    styles = getSampleStyleSheet()

    # Custom styles
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontSize=20,
        leading=24,
        textColor=colors.HexColor('#0F172A'),
        spaceAfter=6,
    )
    subtitle_style = ParagraphStyle(
        'DocSubtitle',
        parent=styles['Normal'],
        fontSize=10,
        leading=14,
        textColor=colors.HexColor('#64748B'),
        spaceAfter=15,
    )
    h1_style = ParagraphStyle(
        'SectionH1',
        parent=styles['Heading2'],
        fontSize=14,
        leading=18,
        textColor=colors.HexColor('#1E3A8A'),
        spaceBefore=14,
        spaceAfter=6,
    )
    body_style = ParagraphStyle(
        'BodyDark',
        parent=styles['Normal'],
        fontSize=9.5,
        leading=14,
        textColor=colors.HexColor('#334155'),
        spaceAfter=8,
    )
    callout_style = ParagraphStyle(
        'Callout',
        parent=styles['Normal'],
        fontSize=9,
        leading=13,
        textColor=colors.HexColor('#047857'),
        backColor=colors.HexColor('#ECFDF5'),
        borderColor=colors.HexColor('#10B981'),
        borderWidth=1,
        borderPadding=6,
        spaceAfter=10,
    )

    story = []

    # Header / Notice
    story.append(Paragraph("APEX INSTITUTE OF HIGHER LEARNING", title_style))
    story.append(Paragraph("Official Student Academic & Policy Handbook (Academic Year 2026–2027)", ParagraphStyle('BoldSub', parent=subtitle_style, fontName='Helvetica-Bold', textColor=colors.HexColor('#1E293B'))))
    story.append(Paragraph("<i>NOTICE: This document is synthetic demonstration data generated for the Agentic AI Engineering Student Support Agent. It does not represent an official legal institutional policy.</i>", subtitle_style))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#CBD5E1'), spaceAfter=15))

    # SECTION 1: Tuition Fee Payment Deadlines
    story.append(Paragraph("Section 1: Tuition Fee Payment Deadlines and Schedules", h1_style))
    story.append(Paragraph(
        "Tuition and academic facility fees are assessed per semester. For the Autumn Semester, regular fee settlement must be completed "
        "no later than November 30 by 23:59 IST. For the Spring Semester, the payment deadline is April 15 by 23:59 IST. "
        "Students opting for the verified two-part installment scheme must pay installment 1 by the regular semester deadline and "
        "installment 2 within 45 calendar days. Payments must be processed through the official Student Financial Services portal via Net Banking, NEFT/RTGS, UPI, or Credit/Debit Cards.",
        body_style
    ))

    # SECTION 2: Late Payment Rules and Financial Holds
    story.append(Paragraph("Section 2: Late Payment Rules, Fines, and Academic Holds", h1_style))
    story.append(Paragraph(
        "A grace period of five (5) business days is automatically applied following any payment deadline. If payment is not recorded "
        "by the end of the grace period, a late penalty fine of INR 500 per business day will be levied up to a maximum cap of INR 5,000. "
        "Accounts unpaid 15 calendar days after the deadline are subject to a Financial Administrative Hold, which temporarily restricts "
        "course enrollment, grade portal access, transcript issuance, and library checkouts until the full balance and accrued fines are cleared.",
        body_style
    ))

    # SECTION 3: Payment Portal Failure and Next Working Day Policy
    story.append(Paragraph("Section 3: Payment Portal Failures, Technical Glitches, and Deadline Extensions", h1_style))
    story.append(Paragraph(
        "If a student experiences a technical failure or outage of the official institutional payment portal on or immediately before an official deadline, "
        "or if funds are debited from the student's bank account without an automated receipt being generated, the student is granted an automatic grace extension. "
        "<b>Can a student pay on the next working day if the portal fails?</b> Yes: If the university payment gateway is unresponsive or errors out on a deadline date, "
        "students are permitted to complete the fee payment on the next working day without incurring any late fee or penalty. "
        "In such occurrences, students must note their bank transaction UTR reference number or screenshot the error screen and submit a support ticket to the Student Financial Services Desk within 24 hours.",
        callout_style
    ))

    # SECTION 4: Scholarships, Fellowships, and Financial Grants
    story.append(Paragraph("Section 4: Scholarship Guidelines, Application Criteria, and Renewal", h1_style))
    story.append(Paragraph(
        "Apex Institute offers multiple scholarship categories: (a) Merit Excellence Fellowship, awarded to students with entrance rank in top 5% or CGPA >= 3.5; "
        "(b) Women in STEM Scholarship, offering up to 50% tuition reduction for female scholars in computing and engineering disciplines; and "
        "(c) Dean's Need-Cum-Merit Grant. Application windows open annually from August 1 to September 15. "
        "Scholarship renewal is subject to continuous full-time enrollment, maintaining a minimum CGPA of 3.50 (for merit categories) or 3.00 (for need grants), "
        "and zero disciplinary violations on the student's institutional record.",
        body_style
    ))

    # SECTION 5: Course Registration, Add/Drop Window, and Programme Change
    story.append(Paragraph("Section 5: Course Registration, Add/Drop Windows, and Programme Transfers", h1_style))
    story.append(Paragraph(
        "Students may adjust their semester course schedules during the official Add/Drop window, which spans the first two (2) calendar weeks of each semester. "
        "Requests to change academic programmes or majors must be initiated prior to the commencement of the second academic year. "
        "Programme transfer requires: (1) a cumulative CGPA of 3.20 or higher, (2) formal written no-objection clearance from the student's current Department Head, "
        "and (3) approval from the Academic Dean of the receiving school. Intra-department course transfers carry an administrative processing fee of INR 1,500.",
        body_style
    ))

    # SECTION 6: Academic Advising and Student Support Services
    story.append(Paragraph("Section 6: Academic Advising, Mentorship, and Student Wellbeing", h1_style))
    story.append(Paragraph(
        "Every enrolled student is assigned a Dedicated Faculty Mentor and an Academic Advisor. Advisor office hours are scheduled weekly for course planning, "
        "internship guidance, and academic difficulty resolution. The Student Learning Assistance Center (SLAC) provides free peer tutoring in mathematics, "
        "computer science, and business communication. For emotional wellbeing and personal counselling, the University Wellness Center is accessible 24/7 "
        "with certified mental health professionals and confidential tele-counseling support.",
        body_style
    ))

    # SECTION 7: Student Grievance Redressal and Appeal Procedures
    story.append(Paragraph("Section 7: Student Grievance Redressal and Formal Appeals", h1_style))
    story.append(Paragraph(
        "Students facing academic disputes, grading irregularities, or administrative issues must first attempt informal resolution with the course instructor "
        "or concerned department administrator within seven (7) days of the incident. If unresolved, a formal grievance may be filed online through the Student "
        "Support Portal addressed to the University Grievance Redressal Committee (GRC). The committee shall investigate and deliver a written verdict within "
        "fourteen (14) calendar days. Appeals against GRC verdicts may be escalated to the University Ombudsman whose ruling is final.",
        body_style
    ))

    # SECTION 8: Explicit Out-of-Scope Statement
    story.append(Paragraph("Section 8: Scope and Out-of-Handbook Inquiries", h1_style))
    story.append(Paragraph(
        "This handbook covers institutional academic policies, tuition billing schedules, and campus student welfare regulations. "
        "Policies regarding international student hostel deposit refunds, visa immigration sponsorships, external study-abroad credit evaluations, "
        "and private residential tenancy agreements are administered independently by external departments (such as the Global Relations Office) "
        "and are NOT governed by or contained within this handbook.",
        body_style
    ))

    # SECTION 9: Admissions Process, Eligibility Criteria, and Required Documentation
    story.append(Paragraph("Section 9: Admissions Process, Eligibility Criteria, and Required Documentation", h1_style))
    story.append(Paragraph(
        "<b>Admissions Overview and Procedure:</b> Admission to academic programmes at Apex Institute is conducted through a structured, merit-based selection process. "
        "The standard admission procedure involves four sequential stages: "
        "(1) Submission of the Online Application Form via the institutional portal (admissions.apexinstitute.edu) along with the application fee; "
        "(2) Evaluation of national entrance examination percentiles (e.g., CAT, GMAT, GRE, GATE) or performance in the Apex Institutional Aptitude Test (AIAT); "
        "(3) Personal Interview (PI) and evaluation of the candidate's Statement of Purpose (SOP) by the Faculty Admissions Panel; and "
        "(4) Release of the Merit List followed by issuance of Provisional Admission Offer Letters.",
        body_style
    ))
    story.append(Paragraph(
        "<b>Mandatory Documents Required for Admission:</b> All provisionally admitted candidates must submit verified physical copies and digital scans of the following documents to the Registrar's Office within fifteen (15) calendar days of seat acceptance: "
        "<br/>1. <b>Academic Certificates:</b> Class 10 and Class 12 passing certificates and consolidated marksheets. "
        "<br/>2. <b>Graduation Records:</b> Official degree completion certificate and semester-wise transcripts for all undergraduate qualifying examinations (minimum 60% aggregate or 6.5 CGPA required). "
        "<br/>3. <b>Entrance Exam Scorecard:</b> Valid authenticated scorecard for CAT, GMAT, GRE, GATE, or AIAT. "
        "<br/>4. <b>Government Photo Identification:</b> Aadhaar Card, Passport, or Voter ID for proof of identity and domestic address. "
        "<br/>5. <b>Institutional Clearance:</b> Official Transfer Certificate (TC) and Migration Certificate issued by the institution last attended. "
        "<br/>6. <b>Conduct / Character Certificate:</b> Issued by the Principal, Dean, or Head of Institution last attended. "
        "<br/>7. <b>Category / Reservation Proof:</b> Valid SC/ST/OBC (Non-Creamy Layer)/EWS certificate issued by a competent revenue authority (if applicable). "
        "<br/>8. <b>Photographs:</b> Four (4) recent passport-sized photographs with white background. "
        "<br/><i>Note: Failure to produce original documents for physical verification prior to the semester commencement date will result in cancellation of the provisional admission offer.</i>",
        body_style
    ))

    doc.build(story)
    print(f"Student Handbook PDF generated successfully at: {pdf_path}")
    return pdf_path


if __name__ == "__main__":
    generate_handbook_pdf()
