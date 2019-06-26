from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.permissions import  IsAdminUser
from rest_framework.generics import ListAPIView, RetrieveAPIView
from .models import VirtualLab
from .serializers import VirtualLabSerializer


# Create your views here.
#VIRTUAL LAB VIEWS
class VirtualLabList(ListAPIView):
    """
    API View that lists all users.

    get: Returns a list of  all Virtual Labs.

    """
    serializer_class = VirtualLabSerializer
    queryset = VirtualLab.objects.all()
    permission_classes = (IsAdminUser,)
    filter_backends = (DjangoFilterBackend,)
    filter_fields = ('code',)


class VirtualLabDetail(RetrieveAPIView):
    """
    API View that lists a User' Detail.

    get: Returns a list of  all reservation records of a logged in user.

    """
    permission_classes = (IsAdminUser,)
    serializer_class = VirtualLabSerializer
    queryset = VirtualLab.objects.all()
    lookup_field = "code"