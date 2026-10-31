"""
Database Seeding Script.
Loads synthetic student, fee, scholarship, and initial support ticket records into SQLite.
"""

import csv
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config.settings import settings
from database.db import init_db, get_db_session
from database.models import Student, FeeRecord, Scholarship, SupportTicket


def seed_database():
    """Populate database with synthetic sample data from CSV."""
    init_db()
    csv_path = settings.DATA_DIR / "sample_students.csv"
    if not csv_path.exists():
        raise FileNotFoundError(f"Sample data file not found at {csv_path}")

    with get_db_session() as session:
        # Check if students already seeded
        existing_students = session.query(Student).count()
        if existing_students == 0:
            with open(csv_path, mode="r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    student = Student(
                        student_id=row["student_id"],
                        name=row["name"],
                        email=row["email"],
                        programme=row["programme"],
                        department=row["department"],
                        academic_year=row["academic_year"],
                        status=row["status"],
                        phone=row["phone"],
                    )
                    session.add(student)

                    # Fee Record
                    fee_record = FeeRecord(
                        student_id=row["student_id"],
                        total_fees=float(row["total_fees"]),
                        amount_paid=float(row["amount_paid"]),
                        outstanding_balance=float(row["outstanding_balance"]),
                        payment_status=row["payment_status"],
                        due_date=row["due_date"],
                        last_payment_date="2026-08-20" if float(row["amount_paid"]) > 0 else None,
                        currency="INR",
                    )
                    session.add(fee_record)

                    # Scholarship Record if applicable
                    if row["scholarship_name"] and row["scholarship_name"] != "None":
                        scholarship = Scholarship(
                            student_id=row["student_id"],
                            scholarship_name=row["scholarship_name"],
                            application_status=row["scholarship_status"],
                            award_amount=float(row["scholarship_amount"]),
                            disbursement_date="2026-09-01" if row["scholarship_status"] == "Approved" else None,
                            details=row["scholarship_details"],
                        )
                        session.add(scholarship)

                # Add a sample initial ticket for testing
                sample_ticket = SupportTicket(
                    ticket_id="TICK-2026-1001",
                    student_id="STU1001",
                    issue_category="Fee Payment",
                    description="Previous semester fee receipt download error on portal.",
                    status="Resolved",
                    priority="Low",
                )
                session.add(sample_ticket)
            print("Database successfully seeded with students, fees, scholarships, and tickets.")
        else:
            print(f"Database already contains {existing_students} students.")

    # Seed User Credentials for Assignment 2
    from security.authn import register_or_update_credential
    from database.models import UserCredential

    with get_db_session() as session:
        # 1. Student Accounts
        student_creds = [
                ("stu1001", "Student#1001!", "Rahul Sharma", "STU1001"),
                ("stu1002", "Student#1002!", "Priya Patel", "STU1002"),
                ("stu1003", "Student#1003!", "Amit Kumar", "STU1003"),
                ("stu1004", "Student#1004!", "Sneha Reddy", "STU1004"),
                ("stu1005", "Student#1005!", "Vikram Singh", "STU1005"),
            ]
        for uname, pwd, dname, sid in student_creds:
            register_or_update_credential(
                username=uname,
                password=pwd,
                role="STUDENT",
                display_name=dname,
                student_id=sid,
            )

        # 2. Support Staff Account
        register_or_update_credential(
            username="support1",
            password="Staff#2026!",
            role="SUPPORT_STAFF",
            display_name="Anita Roy (Senior Support Desk)",
            student_id=None,
        )

        # 3. Administrator Account
        register_or_update_credential(
            username="admin1",
            password="Admin#2026!",
            role="ADMINISTRATOR",
            display_name="Dr. K. Mehta (Academic Dean)",
            student_id=None,
        )
        print("Successfully seeded synthetic user credentials (students, staff, admin) with PBKDF2 hashing.")


if __name__ == "__main__":
    seed_database()

