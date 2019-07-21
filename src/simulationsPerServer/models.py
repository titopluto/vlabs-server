from django.db import models

# Create your models here.
class SimulationsPerServer(models.Model):
    simulations = models.IntegerField(default=1)
