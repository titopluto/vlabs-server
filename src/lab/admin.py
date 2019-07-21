from django.contrib import admin
from .models import Lab


# Register your models here.
class LabAdmin(admin.ModelAdmin):
    list_display = ['code', 'title', 'document']

    class meta:
        model = Lab


admin.site.register(Lab, LabAdmin)

