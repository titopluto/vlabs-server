from django.contrib import admin
from django.contrib.auth.models import Permission
from guardian.admin import GuardedModelAdmin
from .models import Course

# Register your models here.
class CourseAdmin(GuardedModelAdmin):
    list_display = ['code', 'title']

    class meta:
        model = Course


admin.site.register(Course, CourseAdmin)
admin.site.register(Permission)

