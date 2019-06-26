from django.contrib.auth.models import User, Group
from rest_framework import serializers
from guardian.shortcuts import get_objects_for_user
from lab.models import Lab

from course.models import Course
from course.serializers import CourseLabSerializer, CourseVlabAllowedSerializer
from virtualLab.models import VirtualLab
from virlHost.models import VirlHost
from simulation.models import Simulation

from virtualLab.serializers import VirtualLabSerializer








class GroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = Group
        fields = ('name',)

class UserSerializer(serializers.ModelSerializer):
    '''
    A serializer class to represent the User model
    '''
    groups = GroupSerializer(many=True)
    courses_labs = serializers.SerializerMethodField()
    courses_vlabs = serializers.SerializerMethodField()
    simulations = serializers.SerializerMethodField()
    # virtual_labs = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ( 'username',  'first_name', 'last_name', 'email',
                   'groups', 'courses_labs', 'courses_vlabs', 'simulations', 'is_staff', 'is_active' )

    def get_serializer_context(self):
        return {'request': self.request}

    def get_courses_labs(self, obj):
        qs = get_objects_for_user(obj, "course.take_course")
        serializer = CourseLabSerializer(instance=qs, many=True, context={'request': self.context['request']})
        #context={'request': self.context['request']} was used to make request context available for get_document
        #to build the url for the document(pdf_
        return serializer.data

    def get_courses_vlabs(self, obj):
        qs = get_objects_for_user(obj, "course.take_course")
        serializer = CourseVlabAllowedSerializer(instance=qs, many=True, context={'request': self.context['request'],
                                                                                  'user':obj})
        # context={'request': self.context['request']} was used to make request context available for get_document
        # to build the url for the document(pdf_
        return serializer.data

    def get_simulations(self, obj):
        qs = Simulation.objects.filter(user=obj)
        from simulation.serializers import SimulationSerializer
        serializer = SimulationSerializer(instance=qs, many=True)
        return serializer.data

    # def get_virtual_labs(self, obj):
    #     qs = get_objects_for_user(obj, "virtuallab.take_lab")
    #     print("virual labs", qs)
    #     serializer = VirtualLabSerializer(instance=qs, many=True, context={'request': self.context['request']})
    #     return serializer.data








#Course Serializers




#VIRTUAL LAB SERIALIZERS
#
# class CourseSimpleSerializer(serializers.ModelSerializer):
#     """
#     A serializer class to represent course with a limited field
#     """
#
#     # vlabs = serializers.SerializerMethodField()
#
#     class Meta:
#         model = Course
#         fields = ( 'code', 'title')







# class VirtualLabCourseSerializer(serializers.ModelSerializer):
#
#     course = serializers.SerializerMethodField()
#
#     class Meta:
#         model = VirtualLab
#         fields = ('code', 'title', 'course', 'course_vlabs', 'vlabs')
#
#     def get_course(self, obj):
#         print ("self hre", self)
#         qs = obj.course_set.all()
#         # from course.api.serializers import CourseSimpleSerializer
#         serializers = CourseSimpleSerializer(instance=qs, many=True)
#         return serializers.data

from rest_framework.utils import model_meta
from rest_framework.compat import set_many
from rest_framework.serializers import raise_errors_on_nested_writes


#VIRL HOST SERIALIZERS
class VirlHostSerializer(serializers.ModelSerializer):
    class Meta:
        model = VirlHost
        fields = ('ip_address', 'online', 'busy', 'usage')

    def update(self, instance, validated_data):
        raise_errors_on_nested_writes('update', self, validated_data)
        info = model_meta.get_field_info(instance)

        # Simply set each attribute on the instance, and then save it.
        # Note that unlike `.create()` we don't need to treat many-to-many
        # relationships as being a special case. During updates we already
        # have an instance pk for the relationships to be associated with.
        for attr, value in validated_data.items():
            if attr in info.relations and info.relations[attr].to_many:
                set_many(instance, attr, value)
            else:
                setattr(instance, attr, value)
        instance.save(update_fields=self.fields)

        return instance





