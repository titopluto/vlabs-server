from django.shortcuts import render
from rest_framework.generics import ListAPIView, RetrieveUpdateAPIView
from rest_framework.permissions import IsAdminUser
from django_filters.rest_framework import DjangoFilterBackend
from api.serializers import VirlHostSerializer
from .models import VirlHost
from simulation.constants import LAB_PER_VIRL, MAX_BAD_FLAG


# Create your views here.
#VIRLHOST VIEWS

class VirlHostList(ListAPIView):
    """
    API View that lists all users.

    get: Returns a list of  all VIRL Hosts.

    """
    serializer_class = VirlHostSerializer
    queryset = VirlHost.objects.all()
    permission_classes = (IsAdminUser,)
    filter_backends = (DjangoFilterBackend,)
    filter_fields = {
        'online': ['exact'],
        'usage': ['exact','gte', 'lte'],
        'bad_flag': ['gte', 'lte']
    }

class VirlHostReadyList(ListAPIView):
    """
    API View tdyhat lists all users.

    get: Returns a list of  all VIRL Hosts.

    """
    serializer_class = VirlHostSerializer
    queryset = VirlHost.objects.all().filter(online=True, usage__lt=LAB_PER_VIRL,
                           bad_flag__lte=MAX_BAD_FLAG)
    permission_classes = (IsAdminUser,)



class VirlHostDetailUpdate(RetrieveUpdateAPIView):
    """
    API View that give details and update a VIRL Host.

    retrieve: detail of a VIRL Host .

    """
    permission_classes = (IsAdminUser,)
    serializer_class = VirlHostSerializer
    queryset = VirlHost.objects.all()
    lookup_field = "ip_address"
    

# class VirlHostUpdate(UpdateAPIView):
#     """
#         API View that Updates a VIRL Host.
#
#         update: updates a VIRL Host.
#     """
#     serializer_class = VirlHostSerializer
#     queryset = VirlHost.objects.all()
#     lookup_field = "ip_address"

    


