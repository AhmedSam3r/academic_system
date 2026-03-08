from django.contrib import admin

from .models import Enrollment


@admin.register(Enrollment)
class UserCustomAdmin(admin.ModelAdmin):
    model = Enrollment
    list_display = ("id", "grade", "region", "school", "enrolled_at")
    raw_id_fields = ("student",)
    list_filter = ("created_at", "grade", "region")
    ordering = ("id",)
