from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Enrollment
from .serializers import (
    EnrollmentCreateSerializer,
    EnrollmentStatsQuerySerializer,
)


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
        enrollments = serializer.validated_data["enrollments"]

        # TODO implement batch async task using celery
        return Response(
            {"data": enrollments, "msg": "success"},
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

        print(f"data: {data}")

        return Response({"data": data, "msg": "success"})
