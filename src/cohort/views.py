from django.shortcuts import render
from django.contrib.auth.models import User, Group
from rest_framework.generics import ListAPIView
from .serializer import CohortSerializer
from rest_framework.permissions import IsAuthenticated, IsAdminUser



# Create your views here.



class CohortsListView(ListAPIView):
    queryset = Group.objects.all()
    serializer_class = CohortSerializer
    permission_classes = (IsAdminUser,)