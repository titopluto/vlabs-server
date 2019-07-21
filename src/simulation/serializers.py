from rest_framework import serializers
from .models import Simulation
from virtualLab.models import VirtualLab


class SimulationSerializer(serializers.ModelSerializer):

    user = serializers.SlugRelatedField(slug_field="username", read_only=True)
    lab = serializers.SlugRelatedField(queryset=VirtualLab.objects.all(), slug_field="code")
    virl_host = serializers.SlugRelatedField(slug_field="ip_address", read_only=True)
    user_fullname = serializers.SerializerMethodField()

    def get_user_fullname(self, obj):
        user = obj.user
        return "{} {}".format(user.first_name, user.last_name)

    class Meta:
        model = Simulation

        fields = ('user', 'user_fullname', 'lab', 'name', 'virl_host', 'timestamp')
        read_only_fields = ( "name", 'virl_host' )


    def create(self, validated_data):
        print("at validated data --", validated_data)
        user = validated_data.get("user", None)
        lab = validated_data.get("lab", None)
        host = validated_data.get("virl_host")

        # print(**validated_data)

        # host.user = user
        # host.current_lab = lab
        # host.busy = True
        # host.save()

        return Simulation.objects.create(**validated_data)


class SimulationUniqueSerializer(serializers.Serializer):

    lab__code = serializers.CharField()

