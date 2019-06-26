from rest_framework import serializers
from virtualLab.serializers import VirtualLabSerializer
from .models import Course
from lab.serializers import LabSerializer

#LAB SERIALIZERS





class CourseLabSerializer(serializers.ModelSerializer):
    '''
        A serializer class to represent the Course model
    '''
    labs = LabSerializer(many=True)
    # vlabs = VirtualLabSerializer(many=True)
    # labs = serializers.CharField(source="code")

    class Meta:
        model = Course
        fields = ('code', 'title', 'synopsis', 'labs' )


#
# class VLabTest(serializers.ModelSerializer):
#
#     test = serializers.SerializerMethodField()
#
#     class Meta:
#         model = VirtualLab
#         fields = ["test"]
#
#     def get_test(self, obj):
#         user = (self.context['request'].user)
#         # print(obj)
#         # print (user.has_perm("take_lab", obj))
#         # print ("self", self)
#         if (user.has_perm("take_lab", obj)):
#             serializer = VirtualLabSerializer(instance=obj)
#             return serializer.data
#
#         else:
#             return None


class CourseVlabAllowedSerializer(serializers.ModelSerializer):
    '''
        A serializer class to represent the Course model
    '''

    vlabs = serializers.SerializerMethodField()

    class Meta:
        model = Course
        fields = ('code', 'title',  'vlabs' )

    def get_vlabs(self, obj):
        user = self.context['request'].user
        qs = [vlab for vlab in obj.vlabs.all() if (user.has_perm("take_lab", vlab)) ]
        serializer = VirtualLabSerializer(instance=qs, many=True, context={'request': self.context['request']})
        return serializer.data


    # def get_virl(self, obj):
    #     # print ("obk", obj.vlabs)
    #     user = self.context['user']
    #     qs = get_objects_for_user(user, "virtuallab.take_lab")
    #     # print ("get virl", self.context['user'])
    #     serializer = VirtualLabSerializer(instance=qs, many=True)
    #     return serializer.data

class CourseLabVlabAllowedSerializer(serializers.ModelSerializer):
    '''
        A serializer class to represent the Course model
    '''
    labs = LabSerializer(many=True)
    vlabs = serializers.SerializerMethodField()

    class Meta:
        model = Course
        fields = ('code', 'title', 'labs',  'vlabs' )

    def get_vlabs(self, obj):
        user = self.context['request'].user
        qs = [vlab for vlab in obj.vlabs.all() if (user.has_perm("take_lab", vlab)) ]
        print (qs)
        serializer = VirtualLabSerializer(instance=qs, many=True, context={'request': self.context['request']})
        return serializer.data



class CourseAllowedByGroupSerializer(serializers.ModelSerializer):
    '''
        A serializer class to represent the Course model
    '''

    vlabs = serializers.SerializerMethodField()

    class Meta:
        model = Course
        fields = ('code', 'title',  'vlabs' )

    def get_vlabs(self, obj):
        user = self.context['request'].user
        qs = [vlab for vlab in obj.vlabs.all() if (user.has_perm("take_lab", vlab)) ]
        serializer = VirtualLabSerializer(instance=qs, many=True, context={'request': self.context['request']})
        return serializer.data
