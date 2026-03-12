from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from rest_framework.views import APIView
from uuid_utils import uuid7

from .models import Enrollment, EnrollmentBatch
from .serializers import (
    EnrollmentBatchSerializer,
    EnrollmentCreateSerializer,
    EnrollmentStatsQuerySerializer,
)
from .tasks import process_enrollment_batch


class EnrollmentCreateView(GenericAPIView):

    serializer_class = EnrollmentCreateSerializer

    @extend_schema(request=EnrollmentCreateSerializer)
    def post(self, request):
        if request.content_type not in {"application/json"}:
            return Response(
                {"data": None, "msg": "not supported file type"},
                status=400,
            )
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # TODO implement batch async task using celery
        batch_id = str(uuid7())
        data = serializer.data.get("enrollments", [])
        enrollment_batch: EnrollmentBatch = EnrollmentBatch.objects.create(
            id=batch_id,
            total_count=len(data),
        )
        result = process_enrollment_batch.apply_async(
            (batch_id, data),
            countdown=10,
        )
        enrollment_batch.task_id = str(result)
        enrollment_batch.save()

        serializer = EnrollmentBatchSerializer(enrollment_batch)

        return Response(
            {"data": serializer.data, "msg": "success"},
            status=status.HTTP_201_CREATED,
        )


class EnrollmentStatsView(APIView):

    @extend_schema(parameters=[EnrollmentStatsQuerySerializer])
    def get(self, request):

        group_by = request.query_params.get("group_by")
        if group_by not in {"region", "grade"}:
            return Response(
                {"data": None, "msg": "group_by must be region or grade"},
                status=400,
            )

        if group_by == "region":
            data = Enrollment.students_per_region()

        elif group_by == "grade":
            data = Enrollment.students_per_grade()

        return Response({"data": data, "msg": "success"})


# TODO add status endpoint using batch id
