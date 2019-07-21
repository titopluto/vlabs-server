from random import randint
import datetime
from django.conf import settings
from django.db import models
from django.utils.translation import ugettext_lazy as _

from virtualLab.models import VirtualLab
from simulation.models import Simulation


from simulation.constants import LAB_PER_VIRL, MAX_BAD_FLAG
LAB_PER_VIRL = LAB_PER_VIRL




# Create your models here.

class VirlHostQuerySet(models.query.QuerySet):
    def not_assigned(self):
        return self.filter(busy=False, online=True, usage__lt=LAB_PER_VIRL,
                           bad_flag__lte=MAX_BAD_FLAG)


class VirlHostManager(models.Manager):
    def get_queryset(self):
        return VirlHostQuerySet(self.model, using=self._db)

    def random(self):
        #         count = self.aggregate.not_assigned()(count=Count('id'))['count']
        # count = self.all().not_assigned().count()
        # random_index = randint(0, count - 1)
        # print (self.all().not_assigned())
        # return self.all().not_assigned()[random_index]
        # count =  self.all().not_assigned().order_by('usage','last_action_time').count()
        # random_index = randint(0, 1) if count > 0 else 0
        return self.all().not_assigned().order_by('usage', 'last_action_time', 'bad_flag').first()

    def less_busy(self):

        return self.all().not_assigned().order_by('usage')[0]

class VirlHost(models.Model):
    ip_address = models.GenericIPAddressField(_('IP-Address of VIRL Host'), unique=True)
    # current_lab = models.ForeignKey(VirtualLab, related_name="assigned_lab", on_delete=models.CASCADE, blank=True, null=True)
    users = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name="virl_user",  blank=True)
    simulation = models.ManyToManyField(Simulation, blank=True)
    busy = models.BooleanField(default=False)
    usage = models.IntegerField(default=0)
    online = models.BooleanField(default=False)
    bad_flag = models.IntegerField(default=0)
    # last_op_time = models.DateTimeField()
    last_action_time = models.DateTimeField(auto_now=True)


    objects = VirlHostManager()

    def __str__(self):
        return self.ip_address

    @property
    def simulations(self):
        return "#".join([str(sim.admin_display) for sim in self.simulation.all()])

    @property
    def users_list(self):
        return "#".join([user.username for user in self.users.all()])




