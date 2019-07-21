from django.contrib import admin
from .models import SimulationsPerServer

# Register your models here.
class SimulationsPerServerAdmin(admin.ModelAdmin):
    list_display = ['simulations']

    class meta:
        model = SimulationsPerServer


admin.site.register(SimulationsPerServer, SimulationsPerServerAdmin)
