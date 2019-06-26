from django.contrib import admin
from guardian.admin import GuardedModelAdmin
from .models import VirtualLab


# Register your models here.

class VirtualLabAdmin(GuardedModelAdmin):
    list_display = ['code', 'title', 'synopsis', 'document', 'topology']

    class Meta:
        model = VirtualLab

admin.site.register(VirtualLab, VirtualLabAdmin)