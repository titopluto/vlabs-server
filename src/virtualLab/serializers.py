from rest_framework import serializers
from .models import VirtualLab

class VirtualLabSerializer(serializers.ModelSerializer):

    document = serializers.SerializerMethodField()
    topology = serializers.SerializerMethodField()

    class Meta:
        model = VirtualLab
        fields = ('id','code', 'title', 'synopsis', 'document', 'topology')

    def get_document(self, obj):
        if obj.document:
            return self.context['request'].build_absolute_uri(obj.document.url)
        else:
            return None

    def get_topology(self, obj):
        if obj.topology:
            return self.context['request'].build_absolute_uri(obj.topology.url)
        else:
            return None