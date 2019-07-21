from rest_framework import serializers
from django.contrib.auth.models import Group




class CohortSerializer(serializers.ModelSerializer):
    class Meta:
        model = Group
        fields = ('name',)
