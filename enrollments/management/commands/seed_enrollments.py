import logging
import random

from django.core.management.base import BaseCommand
from django.db import transaction
from faker import Faker
from uuid_utils import uuid7

from enrollments.models import Enrollment, EnrollmentBatch
from students.models import Student

logger = logging.getLogger(__name__)

fake = Faker()

TOTAL_RECORDS = 10_000_000
BATCH_SIZE = 10_000


class Command(BaseCommand):
    help = "Populate Enrollment table with fake data"

    def handle(self, *args, **kwargs):

        logger.info("Creating students...")

        buffer = []
        TOTAL_STUDENTS = 1_000_000
        for i in range(TOTAL_STUDENTS):
            email = f"{fake.email()}_{i}_1"
            student = Student(
                name=fake.name(),
                email=email,
            )

            buffer.append(student)

            if len(buffer) >= BATCH_SIZE:
                self.insert_students(buffer)
                # student_ids.extend(ids)
                buffer = []

                if i % 100_000 == 0:
                    logger.info(f"Created {i} students")

        if buffer:
            self.insert_students(buffer)

        students_ids = list(Student.objects.values_list("id", flat=True))

        if not students_ids:
            logger.info("No students found")
            return

        batch = EnrollmentBatch.objects.create(
            id=str(uuid7()),
            total_count=TOTAL_RECORDS,
            processed_count=TOTAL_RECORDS,
            status="processed",
        )

        regions = [
            "Cairo",
            "Alexandria",
            "Giza",
            "Luxor",
            "Aswan",
            "Mansoura",
            "Tanta",
            "Suez",
            "Ismailia",
            "Port Said",
        ]

        grades = [
            "Grade 1",
            "Grade 2",
            "Grade 3",
            "Grade 4",
            "Grade 5",
            "Grade 6",
            "Grade 7",
            "Grade 8",
            "Grade 9",
            "Grade 10",
            "Grade 11",
            "Grade 12",
        ]

        schools = [
            "Nile Academy",
            "Al Azhar School",
            "Cairo STEM",
            "Future Language School",
            "British International Cairo",
            "Alexandria Modern School",
            "Giza National School",
            "Misr Language School",
            "El Nasr Boys School",
            "Ramses College",
        ]

        statuses = [
            "processed",
            "processed",
            "processed",
            "processed",
            "failed",
        ]  # 80/20

        enrollment_buffer = []
        # TODO fix the script
        for i in range(0, TOTAL_RECORDS):
            student_id = students_ids[i]
            # student_id = student_id + i
            enrollment = Enrollment(
                batch=batch,
                student_id=student_id,
                grade=random.choice(grades),
                region=random.choice(regions),
                school=random.choice(schools),
                status=random.choice(statuses),
            )

            enrollment_buffer.append(enrollment)

            if len(enrollment_buffer) >= BATCH_SIZE:
                self.insert_enrollments(enrollment_buffer)
                enrollment_buffer = []

                if i % 100_000 == 0:
                    logger.info(f"Inserted {i} records")

        if enrollment_buffer:
            self.insert_enrollments(enrollment_buffer)

        logger.info("Done inserting 10M enrollments")

    @staticmethod
    @transaction.atomic
    def insert_students(records):
        Student.objects.bulk_create(records, batch_size=10_000)

    @staticmethod
    @transaction.atomic
    def insert_enrollments(records):
        Enrollment.objects.bulk_create(records, batch_size=10_000)
