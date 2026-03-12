from django.contrib import admin

from .models import Student


@admin.register(Student)
class UserCustomAdmin(admin.ModelAdmin):
    model = Student
    list_display = ("id", "email", "name", "verified")
    list_filter = ("email",)
    ordering = ("id",)
