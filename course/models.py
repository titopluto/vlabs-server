from django.db import models
from lab.models import Lab
from virtualLab.models import VirtualLab
from django.utils.translation import ugettext_lazy as _


# Create your models here.
class Course(models.Model):
    code = models.CharField(_("Course Code"), max_length=10)
    title = models.CharField(max_length=50)
    synopsis = models.TextField(_("Synopsis"))
    labs = models.ManyToManyField(Lab, blank=True)
    vlabs = models.ManyToManyField(VirtualLab, related_name="course_vlabs", verbose_name=_("VIRL labs"), blank=True)

    def __str__(self):
        return "{0}".format(self.code)

    class Meta:
        permissions = ( ("take_course", "Group/User can take this course"),)