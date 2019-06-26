from django.contrib import admin
from .models import VirlHost
from simulation.models import Simulation

# Register your models here.

class SimulationInline(admin.TabularInline):
    model = VirlHost.simulation.through


class VirlHostAdmin(admin.ModelAdmin):

    # inlines = [ SimulationInline, ]
    list_display = ['ip_address', 'users_display',
                    'simulations_display', 'busy',
                    'usage', 'online', 'last_action_time', 'bad_flag']


    class Meta:
        model = VirlHost

    def simulations_display(self, obj):
        simulations = obj.simulations
        split = simulations.split("#")

        return "<br>".join(split)

    simulations_display.allow_tags = True

    def users_display(self, obj):
        users = obj.users_list
        split = users.split("#")

        return "<br>".join(split)

    users_display.allow_tags = True


admin.site.register(VirlHost, VirlHostAdmin)