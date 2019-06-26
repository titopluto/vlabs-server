from django.db import models

# Create your models here.
def user_directory_path(instance, filename):
    # file will be uploaded to MEDIA_ROOT/user_<id>/<filename>
    return 'lab_manuals/{0}/{1}.pdf'.format(instance.code, instance.code)

class Lab(models.Model):
    code = models.CharField(max_length=15)
    title = models.CharField(max_length=50)
    synopsis = models.TextField(default="")
    document = models.FileField(upload_to=user_directory_path)

    def __str__(self):
        return '{0}: {1}'.format(self.code, self.title)


