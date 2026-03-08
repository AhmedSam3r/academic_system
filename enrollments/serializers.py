from rest_framework import serializers


class EnrollmentStatsQuerySerializer(serializers.Serializer):
    group_by = serializers.ChoiceField(
        choices=["region", "grade"],
        help_text="Field used to group students",
    )


class EnrollmentItemSerializer(serializers.Serializer):
    student_name = serializers.CharField(min_length=3, max_length=255)
    region = serializers.CharField(min_length=3, max_length=255)
    grade = serializers.CharField(min_length=3, max_length=255)
    grade = serializers.CharField(min_length=3, max_length=255)


class EnrollmentCreateSerializer(serializers.Serializer):
    enrollments = EnrollmentItemSerializer(many=True)
