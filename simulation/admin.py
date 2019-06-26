from django.contrib import admin
from .models import Simulation

# Register your models here.
class SimulationAdmin(admin.ModelAdmin):
    list_display = ['name', 'user', 'lab', 'virl_host', 'username', 'password', 'timestamp']

    class meta:
        model = Simulation


admin.site.register(Simulation, SimulationAdmin)
