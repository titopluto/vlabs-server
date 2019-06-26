from django.db import models
from django.contrib.auth.models import User
# from virlHost.models import VirlHost
from virtualLab.models import VirtualLab

# Create your models here.

# Create your models here.
class SimulationQuerySet(models.query.QuerySet):

    def get_user(self, user):
        return self.filter(user=user)


class SimulationManager(models.Manager):
    def get_queryset(self):
        return SimulationQuerySet(self.model, using=self._db)

    def all_user(self, user):
        return self.get_queryset().get_user(user).order_by('-timestamp')

class Simulation(models.Model):
    name = models.CharField(max_length=100)
    user = models.ForeignKey(User)
    lab = models.ForeignKey('virtualLab.VirtualLab', related_name='vlab', on_delete=models.CASCADE)
    virl_host = models.ForeignKey('virlHost.VirlHost', related_name='server', on_delete=models.CASCADE)
    username = models.CharField(max_length=100)
    password = models.CharField(max_length=100)
    timestamp = models.DateTimeField(auto_now_add=True)

    objects = SimulationManager()

    def __str__(self):
        return '{0}:{1}:{2}'.format(self.user, self.virl_host, self.lab)

    @property
    def admin_display(self):
        return '{0}({1})'.format(self.lab, self.user)
