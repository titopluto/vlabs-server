from django.contrib.auth.models import User
from rest_framework.generics import ListAPIView, RetrieveAPIView
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from django.shortcuts import get_object_or_404 as _get_object_or_404
from django.core.exceptions import ValidationError
from django.http import Http404


from .serializers import UserSerializer
from .permissions import IsAdminOrIsOwner

from .serializers import (  VirlHostSerializer)

from course.serializers import LabSerializer

from course.models import Course
from lab.models import Lab
from virtualLab.models import VirtualLab


def get_object_or_404(queryset, *filter_args, **filter_kwargs):
    """
    Same as Django's standard shortcut, but make sure to also raise 404
    if the filter_kwargs don't match the required types.
    """
    try:
        return _get_object_or_404(queryset, *filter_args, **filter_kwargs)
    except (TypeError, ValueError, ValidationError):
        raise Http404

# Create your views here.
class UserList(ListAPIView):
    """
    API View that lists all users.

    get: Returns a list of  all reservation records of a logged in user.

    """
    serializer_class = UserSerializer
    queryset = User.objects.all()
    permission_classes = (IsAdminUser,)


class UserSelfDetail(RetrieveAPIView):
    """
    API View that lists a User' Detail.

    get: Returns a list of  all reservation records of a logged in user.

    """
    permission_classes = (IsAuthenticated,)
    serializer_class = UserSerializer
    queryset = User.objects.all()
    # lookup_field = "username" # not needed cos i overwrote get_object

    # def dispatch(self, request, *args, **kwargs):
    #     self.lookup_field = self.request.user.username
    #     # super(UserSelfDetail, self).dispatch(request, *args, **kwargs)

    def get_object(self):
        queryset = self.get_queryset()
        lookup_field =  {'username':self.request.user}
        obj = get_object_or_404(queryset, **lookup_field)
        self.check_object_permissions(self.request, obj)
        return obj


class UserDetail(RetrieveAPIView):
    """
    API View that lists a User' Detail.

    get: Returns a list of  all reservation records of a logged in user.

    """
    permission_classes = (IsAdminUser,)
    serializer_class = UserSerializer
    queryset = User.objects.all()
    lookup_field = "username"




#COURSE VIEWS






#LAB VIEWS
class LabList(ListAPIView):
    """
        API View that lists all course.

        get: Returns a list of  all reservation records of a logged in user.

        """
    serializer_class = LabSerializer
    queryset = Lab.objects.all()
    permission_classes = (IsAuthenticated,)



class LabDetail(RetrieveAPIView):
    """
        API View that lists all course.

        get: Returns a list of  all reservation records of a logged in user.

        """
    serializer_class = LabSerializer
    queryset = Lab.objects.all()
    permission_classes = (IsAuthenticated,)
    lookup_field = "code"








