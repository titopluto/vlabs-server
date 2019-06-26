from django.contrib.auth.models import Group
from rest_framework.permissions import  IsAuthenticated
from rest_framework.generics import ListAPIView, RetrieveAPIView
from guardian.shortcuts import get_group_perms
from .models import VirtualLab
from .serializers import CourseLabSerializer, CourseLabVlabAllowedSerializer,\
    CourseVlabAllowedSerializer, CourseAllowedByGroupSerializer
from .models import Course

# Create your views here.


class CourseLabList(ListAPIView):
    """
        API View that lists all course.

        get: Returns a list of  all reservation records of a logged in user.

        """
    serializer_class = CourseLabSerializer
    queryset = Course.objects.all()
    permission_classes = (IsAuthenticated,)

    # def list(self, request):
    #     # Note the use of `get_queryset()` instead of `self.queryset`
    #     queryset = self.get_queryset()
    #     serializer = CourseSerializer(queryset, context={"request": request}, many=True)
    #     return Response(serializer.data)


class CourseVlabList(ListAPIView):
    """
        API View that lists all course.

        get: Returns a list of  all reservation records of a logged in user.

        """
    serializer_class = CourseVlabAllowedSerializer
    queryset = Course.objects.all()
    permission_classes = (IsAuthenticated,)


class CourseLabVlabList(ListAPIView):
    """
        API View that lists all course.

        get: Returns a list of  all reservation records of a logged in user.

        """
    serializer_class = CourseLabVlabAllowedSerializer
    queryset = Course.objects.all()
    permission_classes = (IsAuthenticated,)


class CourseDetail(RetrieveAPIView):
    """
        API View that lists all course.

        get: Returns a list of  all reservation records of a logged in user.

        """
    serializer_class = CourseLabSerializer
    queryset = Course.objects.all()
    permission_classes = (IsAuthenticated,)
    lookup_field = "code"


class CourseByGroup(ListAPIView):
    """
        API View that lists all course.

        get: Returns a list of  all reservation records of a logged in user.

        """
    serializer_class = CourseAllowedByGroupSerializer
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        group_name = self.kwargs['group']
        try:
            group = Group.objects.get(name=group_name)
            return [course for course in Course.objects.all() if 'take_course' in get_group_perms(group, course)]
        except:
            return Course.objects.all()
