import logging
import uuid
from typing import Any

from celery import shared_task
from celery.exceptions import Reject

from enrollments import utils

logger = logging.getLogger(__name__)

batch_size = 500
main_queue_name = "main"
main_routing_key = "main"
dlq_routing_key = f"{main_routing_key}-dlq"
dlq_queue_name = f"{main_queue_name}-dlq"
retry_queue_name = f"{main_queue_name}-retry"
retry_routing_key = f"{main_routing_key}-retry"


@shared_task(
    bind=True,
    acks_late=True,
)
def process_enrollment_batch(
    self,
    batch_id: uuid.UUID,
    enrollment_data: list[Any],
):
    max_retries = 3
    headers = self.request.headers or {}
    retries = headers.get("x-retries", 0)
    logger.info(
        f"processing batch_id: {batch_id} headers: {headers} with enrollment_data: {enrollment_data}",  # noqa: E501
    )
    if retries >= max_retries:
        logger.info(f"retries exceeded batch_id: {batch_id} headers:{headers}")
        raise Reject("retries exceeded", requeue=False)

    try:
        total_count = len(enrollment_data)
        task_id = self.request.id
        logger.info(
            f"processing enrollments with batch_id: {batch_id} with task_id: {task_id}",  # noqa: E501
        )

        # first: ensure batch is correct and update status
        batch = utils.validate_enrollment_batch(batch_id, task_id)

        if not batch:
            return

        # second: ensure students exist
        student_results = utils.create_or_update_students(enrollment_data)

        # third: create enrollments for students
        # finally: update batch status
        utils.create_enrollments(
            batch_id=batch_id,
            enrollment_data=enrollment_data,
            persisted_map=student_results["persisted_map"],
            student_objects=student_results["student_objects"],
            total_count=total_count,
        )

        return True

    except Exception as exc:
        logger.exception(f"exception of batch id: {batch_id} ... {exc} ")

        if retries < max_retries:
            logger.info(
                f"Sending the task with batch_id: {batch_id} to retry queue"
            )  # noqa: E501
            headers.update({"x-retries": retries + 1})
            # without countdown
            self.apply_async(
                args=[batch_id, enrollment_data],
                queue=retry_queue_name,
                routing_key=retry_routing_key,
                headers=headers,
            )

    return True
