from django.contrib import admin

from .models import Enrollment, EnrollmentBatch


@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    model = Enrollment
    list_display = ("id", "grade", "region", "school", "enrolled_at")
    raw_id_fields = ("student",)
    list_filter = ("created_at", "grade", "region")
    ordering = ("id",)


@admin.register(EnrollmentBatch)
class EnrollmentBatchAdmin(admin.ModelAdmin):
    model = EnrollmentBatch
    list_display = ("id", "status", "total_count", "processed_count", "failed_count")
    list_filter = ("created_at", "status")
    ordering = ("id",)
