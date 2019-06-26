from rest_framework import serializers
from .models import Lab


class LabSerializer(serializers.ModelSerializer):
    '''
        A serializer class to represent the Lab model
    '''
    document = serializers.SerializerMethodField()


    class Meta:
        model = Lab
        fields = ('code', 'title', 'synopsis', 'document')

    def get_document(self, obj):
        return self.context['request'].build_absolute_uri(obj.document.url)