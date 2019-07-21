from django.db import models


# Create your models here.
def user_directory_path_document(instance, filename):
    # file will be uploaded to MEDIA_ROOT/user_<id>/<filename>
    return 'virtual_labs/document/{0}/{1}.pdf'.format(instance.code, instance.code)

def user_directory_path_topology(instance, filename):
    # file will be uploaded to MEDIA_ROOT/user_<id>/<filename>
    return 'virtual_labs/topology/{0}/{1}.virl'.format(instance.code, instance.code)


class VirtualLab(models.Model):
    code = models.CharField(max_length=15)
    title = models.CharField(max_length=50)
    synopsis = models.TextField(default="")
    document = models.FileField(upload_to=user_directory_path_document,
                                null=True, blank=True,default="")
    topology = models.FileField(upload_to=user_directory_path_topology, null=True)

    class Meta:
        permissions = ( ("take_lab", "Group/User can take this VIRL Lab"),)

    def __str__(self):
        return '{0}: {1}'.format(self.code, self.title)

    def obj_permission(self):
        return {"tito" :"titmo"}