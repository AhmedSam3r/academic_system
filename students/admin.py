from django.contrib import admin

from .models import Student


@admin.register(Student)
class UserCustomAdmin(admin.ModelAdmin):
    model = Student
    list_display = ("id", "email", "name", "verified", "enrolled_at")
    list_display = (
        "id", "email", "name", "verified", "is_staff",
        "created_at", "updated_at", "blocked",
    )
    list_filter = ('email', )
    ordering = ('id',)
