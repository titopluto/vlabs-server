import time
import datetime
import requests
from requests.auth import HTTPBasicAuth
from django.contrib.auth.models import User
from django.shortcuts import render
from rest_framework.generics import get_object_or_404
from django.http import HttpResponse
from django.db.models import Q
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.views import APIView
from rest_framework.generics import ListAPIView, CreateAPIView, ListCreateAPIView, RetrieveDestroyAPIView, RetrieveUpdateAPIView, RetrieveAPIView, GenericAPIView
from rest_framework.mixins import ListModelMixin, CreateModelMixin, DestroyModelMixin, RetrieveModelMixin
from rest_framework.response import Response
from rest_framework import status
from django_filters.rest_framework import DjangoFilterBackend
from django.shortcuts import get_list_or_404


from .permissions import IsAdminOrIsOwner
from simulation.models import Simulation
from .serializers import SimulationSerializer, SimulationUniqueSerializer
from .constants import VIRL_USERNAME, VIRL_PASSWORD

from .engine import SimEngine

from virlHost.models import VirlHost
from virtualLab.models import VirtualLab


from .constants import LAB_PER_VIRL, MAX_BAD_FLAG

LAB_PER_VIRL = LAB_PER_VIRL

from rest_framework.parsers import MultiPartParser



# Create your views here.

def v_get(virl_ip, append_url="", **params):
    auth = HTTPBasicAuth(VIRL_USERNAME, VIRL_PASSWORD)
    url = "http://%s:19399/%s" % (virl_ip, append_url)
    params = params
    response = requests.get(url, auth=auth, params=params)
    return response

def reset_virl_host(virl_host, user):
    virl_host.users.remove(user)
    virl_host.busy = False
    virl_host.usage -= 1
    virl_host.bad_flag += 1
    virl_host.save()
    return


def perform_sanitization(simulation):
    user = simulation.user
    virl_host = simulation.virl_host
    virl_host.users.remove(user)
    virl_host.simulation.remove(simulation)
    virl_host.busy = False
    virl_host.usage -= 1
    virl_host.bad_flag = 0
    virl_host.save()
    simulation.delete()
    return


class SimulationSelfList(ListAPIView):

    serializer_class = SimulationSerializer
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        return Simulation.objects.all().filter(user=self.request.user)


class SimulationUserList(ListAPIView):
    serializer_class = SimulationSerializer
    permission_classes = (IsAdminUser,)


    def get_queryset(self):
        username = self.kwargs['username']
        return Simulation.objects.all().filter(user__username=username)

class SimulationList (ListAPIView):

    queryset = Simulation.objects.all()
    serializer_class = SimulationSerializer
    permission_classes = (IsAdminUser,)
    filter_backends = (DjangoFilterBackend,)
    filter_fields = ('lab__code',)


class SimulationListUnique(ListAPIView):
    serializer_class = SimulationUniqueSerializer
    permission_classes = (IsAdminUser,)

    def get_queryset(self):
        return Simulation.objects.all().values('lab__code').distinct()



class SimulationRetrieveByID (RetrieveAPIView):

    queryset = Simulation.objects.all()
    serializer_class = SimulationSerializer
    permission_classes = (IsAdminUser,)
    lookup_field = "name"

    # i used the  simEngine.node_access to return a simulation because i am only interested
    # to check if the simulation exist on the VIRL server. if it does not exist then it will
    # return a 404 error, so i can perform sanitization on the django database.
    # if it exist, then i can return the simulation from the django database

    def retrieve(self, request, *args, **kwargs):
        simulation = self.get_object()
        sim_name = simulation.name
        user = request.user
        virl_ip = simulation.virl_host.ip_address
        mode = request.GET.get("mode", None)

        simEngine = SimEngine(VIRL_USERNAME, VIRL_PASSWORD, virl_ip, sim_name)

        try:
            response = simEngine.nodes_links(mode=mode)
        except:
            error = {"error": "Error encountered accessing  your simulation nodes",
                     "detail": "NO RESPONSE! from the VIRL server. The Server IP may not be reachable"}
            return Response(error, status=status.HTTP_504_GATEWAY_TIMEOUT)

        if response.status_code == 200:  # launch was successful

            serializer = self.get_serializer(simulation)
            return Response(serializer.data)

        elif response.status_code == 401:
            error_json = response.json()
            error = {'error': error_json['cause'], 'detail': error_json['details']}
            return Response(error, status=status.HTTP_403_FORBIDDEN)

        elif response.status_code == 404:
            # simulation not found on server so we should delete from database
            simulation = self.get_object()
            perform_sanitization(simulation)

            error_json = response.json()
            error = {'error': error_json['cause'], 'detail': "i couldn't find the simulation  on server, but performed sanitization"}
            return Response(error, status=status.HTTP_404_NOT_FOUND)

        elif response.status_code == 503:
            error_json = response.json()
            error = {'error': error_json['cause'], 'detail': error_json['details']}
            return Response(error, status=status.HTTP_403_FORBIDDEN)

        else:
            error = {'error': 'Unknown Error', 'detail': 'I could not retreive your simulation data'}
            return Response(error, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class SimulationNodesByLab(RetrieveAPIView):
    queryset = Simulation.objects.all()
    serializer_class = SimulationSerializer
    permission_classes = (IsAdminOrIsOwner,)
    lookup_field = 'user__username'

    def get_object(self):
        filter_kwargs = {'lab__code': self.kwargs['lab']}
        obj = get_list_or_404(self.queryset, **filter_kwargs)[0]
        self.check_object_permissions(self.request, obj)
        return obj

    def retrieve(self, request, *args, **kwargs):

        simulation = self.get_object()
        sim_name = simulation.name

        nodesMonitorLinkResponse = SimulationNodesLinks.as_view()(request, name=sim_name)
        return nodesMonitorLinkResponse
        # print(nodesMonitorLinkData)
        # nodesMonitorLinkData = nodesMonitorLinkResponse.data
        # return Response(nodesMonitorLinkData, status=status.HTTP_200_OK)

class SimulationCreate(CreateAPIView):
    '''
    A class to create a simulation after making an API call to a chosen  VIRL server
    It has 2 modes:
    1. VIRL topology is got from an exisiting VitualLab Object and the topolgy is got from the object
    2. self service mode: it receives a blob file, as a request..  containing the VIRL topology
    '''

    queryset = Simulation.objects.all()
    serializer_class = SimulationSerializer
    permission_classes = (IsAuthenticated,)

    def register_simulation(self, request):
        '''
        method to register the simulation in the database once VIRL server returns code 200
        :param request:
        :return: a Response object to display back to the User
        '''
        if request.data.get('lab',None) is not None:
            serializer = self.get_serializer(data=request.data)
        else:
            # if using self service mode
            serializer = self.get_serializer(data={'lab':'self_service'})

        serializer.is_valid(raise_exception=True)
        created_simulation = self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)

        # Add simulation to sever and sanitize the virl server for future use.
        self.virl_host.simulation.add(created_simulation)
        self.virl_host.busy = False
        self.virl_host.bad_flag = 0
        self.virl_host.save()
        # self.virl_host.last_op_time = datetime.datetime.now()
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def create(self, request, *args, **kwargs):
        #get the model attribute needed to create simulation object
        if kwargs.get('user'):
            user_str = kwargs.get('user')
            user, created = User.objects.get_or_create(username=user_str)
            self.user = user
        else:
            user = request.user
            self.user = user
        try:
            self.lab = VirtualLab.objects.get(code=self.request.data.get("lab"))
        except:
            # get_or_create always returns a tuple
            self.lab, created = VirtualLab.objects.get_or_create(code="self_service")

        if VirlHost.objects.filter(users__id=user.id, busy=True ).exists():
            error = {"error": "Conditions not met",
                     "detail": "We are still working on your previous request, Please be Patient"}
            return Response(error, status=status.HTTP_412_PRECONDITION_FAILED)

        if VirlHost.objects.filter(users__id=user.id, simulation__user=user ).exists():
            error = {"error":"Conditions not met", "detail": "You have an Active Simulation. Please Deactivate and try again"}
            return Response(error, status=status.HTTP_412_PRECONDITION_FAILED)

        if VirlHost.objects.filter(users__id=user.id ).exists():
            error = {"error":"Conditions not met", "detail": "You are already assigned a server, please notify a staff of this error"}
            return Response(error, status=status.HTTP_412_PRECONDITION_FAILED)

        if VirlHost.objects.filter(~Q(users__id=user.id), busy=False, usage__lt=LAB_PER_VIRL,
                                   online=True, bad_flag__lte=MAX_BAD_FLAG).exists():

            self.virl_host = VirlHost.objects.random()
            self.virl_host.users.add(user)
            self.virl_host.busy = True
            self.virl_host.usage += 1
            self.virl_host.save()
            # self.virl_host.last_op_time = datetime.datetime.now()

        else:
            error = {"error":"Conditions not met", "detail": "No Available VIRL HOST to spin up your simulation "}
            return Response(error, status=status.HTTP_412_PRECONDITION_FAILED)

        virl_ip = str(self.virl_host.ip_address)

        try:
            topology_path = str(self.lab.topology.url.lstrip("/"))
        except:
            topology_path = None

        api_sim_file = request.data.get('file', None)
        self.sim_name = "{0}-{1}".format(str(self.lab.code), str(user.username))

        # try:
        #     self.sim_name = "{0}-{1}".format(str(self.lab.code), str(user.username))
        # except:
        #     self.sim_name = "{0}-{1}".format(api_sim_file.split(".")[0], str(user.username))


        simulation = SimEngine(VIRL_USERNAME, VIRL_PASSWORD, virl_ip, self.sim_name, topology_path, api_sim_file=api_sim_file)

        print("creating {} SIM for {} on {}".format(self.sim_name, user, virl_ip))

        try:
            response = simulation.launch(expiry=960)
            if response.status_code == 200:  # launch was successful
                return self.register_simulation(request)
        except:
            try:
                while True:
                    print("<===> rechecking if simulation exists <====>", " error at initial response")
                    time.sleep(10)
                    response = simulation.confirm_simulation()
                    if response.status_code == 200:
                        msg= response.json()
                        print(f'msg state ==> {msg["state"]}')
                        if msg['state'] =='ACTIVE':
                            print("recheck successful for user {} on {}".format(user, virl_ip))
                            return self.register_simulation(request)
                    error = {'error': 'No simulation created during rechecking',
                             'detail': 'Rechecking Failed for {} on {}'.format(user, virl_ip)}
                    print (error)
                    reset_virl_host(self.virl_host, user)
                    # raise RuntimeError("Error: No simulation created during rechecking")
                    return Response(error, status=status.HTTP_417_EXPECTATION_FAILED)
            except:
                reset_virl_host(self.virl_host, user)

                error = {"error": "Your simulation launching Failed",
                         'detail':'NO RESPONSE! from the VIRL server. The Server IP({}) may not be reachable \n OR VIRL Topology XML is not Valid! '.format(virl_ip) }
                # print(f"here: {error}")
                return Response(error, status=status.HTTP_504_GATEWAY_TIMEOUT)

        if response.status_code == 400:
            reset_virl_host(self.virl_host, user)
            error_json = response.json()
            error = {'error': error_json['cause'], 'detail': error_json['details'] + ". Server detail: {}".format(virl_ip)}
            return Response(error, status=status.HTTP_400_BAD_REQUEST)

        elif response.status_code == 401:
            reset_virl_host(self.virl_host, user)
            error_json = response.json()
            error = {'error': error_json['cause'], 'detail':error_json['details'] + ". Server detail: {}".format(virl_ip)  }
            return Response(error, status=status.HTTP_403_FORBIDDEN)

        elif response.status_code == 403:
            reset_virl_host(self.virl_host, user)
            error_json = response.json()
            error = {'error': error_json['cause'], 'detail': error_json['details'] + ". Server detail: {}".format(virl_ip)}
            return Response(error, status=status.HTTP_403_FORBIDDEN)

        elif response.status_code == 409:
            reset_virl_host(self.virl_host, user)
            error_json = response.json()
            error = {'error': error_json['cause'], 'detail': error_json['details'] + ". Server detail: {}".format(virl_ip)}
            return Response(error, status=status.HTTP_409_CONFLICT)

        elif response.status_code == 503:
            reset_virl_host(self.virl_host, user)
            error_json = response.json()
            error = {'error': error_json['cause'], 'detail': error_json['details'] + ".Server detail: {}".format(virl_ip)}
            return Response(error, status=status.HTTP_503_SERVICE_UNAVAILABLE)

        else:
            try:
                print("from Last Else", "Trying recreating simulatuon")
                response = simulation.confirm_simulation()
                if response.status_code == 200:
                    msg = response.json()
                    if msg['state'] == 'ACTIVE':
                        print("recheck successful for user {} on {}".format(user, virl_ip))
                        return self.register_simulation(request)
                else:
                    reset_virl_host(self.virl_host, user)
                    raise RuntimeError("Error: No simulation created during rechecking on {}".format(virl_ip))
            except:
                reset_virl_host(self.virl_host, user)
                error = { 'error': "Unknown Error!", 'detail':'Could not define the type of error.\n Maybe license not activated. Server detail: {}'.format(virl_ip)}
                return  Response(error, status=status.HTTP_507_INSUFFICIENT_STORAGE)


    def perform_create(self, serializer):
        print("at perform create")
        user = self.request.user
        simulation_name = self.sim_name

        # self.virl_host.user = user
        # self.virl_host.current_lab = self.lab
        # self.virl_host.save()
        # print("self.sim_name", self.lab)
        # print("self.lab object-id", self.lab.id)
        sim_serialized = serializer.save(user=self.user, lab=self.lab, virl_host=self.virl_host, name=simulation_name)
        return sim_serialized




class SimulationRetrieveDestroy(RetrieveDestroyAPIView):

    queryset = Simulation.objects.all()
    serializer_class = SimulationSerializer
    permission_classes = (IsAdminOrIsOwner,)
    lookup_field = "name"

    def delete(self, request, *args, **kwargs):
        simulation = self.get_object()
        sim_name = simulation.name
        virl_ip = simulation.virl_host.ip_address

        simEngine = SimEngine(VIRL_USERNAME, VIRL_PASSWORD, virl_ip, sim_name)

        try:
            response = simEngine.stop()
        except:
            error = {"error": "Simulation Stop Failed",
                     'detail': 'NO RESPONSE! from the VIRL server. The Server IP may not be reachable'}
            return Response(error, status=status.HTTP_504_GATEWAY_TIMEOUT)

        if response.status_code == 200:  # launch was successful
            self.perform_destroy(simulation)

            return Response({"detail":"Simulation was successfully deleted"}, status=status.HTTP_204_NO_CONTENT)

        elif response.status_code == 400:
            error_json = response.json()
            error = {'error': error_json['cause'], 'detail': error_json['details']}
            return Response(error, status=status.HTTP_400_BAD_REQUEST)

        elif response.status_code == 401:
            error_json = response.json()
            error = {'error': error_json['cause'], 'detail': error_json['details']}
            return Response(error, status=status.HTTP_403_FORBIDDEN)

        elif response.status_code == 404:
            # simulation not found on server so we should delete from database
            self.perform_destroy(simulation)
            error_json = response.json()
            error = {'error': error_json['cause'], 'detail': "i couldn't find simulation on server, but performed sanitization"}
            return Response(error, status=status.HTTP_404_NOT_FOUND)

        else:
            error = { 'error': 'Unknown Error', 'detail': 'I couldn;t stop the simulation'}
            return  Response(error, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


    def perform_destroy(self, instance):
        simulation = instance
        user = simulation.user
        virl_host = simulation.virl_host

        virl_host.users.remove(user)
        # virl_host.current_lab = None
        virl_host.simulation.remove(simulation)
        virl_host.busy = False
        virl_host.usage -= 1
        virl_host.save()

        instance.delete()



class SimulationDestroyALL(ListAPIView):

    queryset = Simulation.objects.all()
    serializer_class = SimulationSerializer
    permission_classes = (IsAuthenticated,)

    def list(self, request, *args, **kwargs):

        simulations = self.get_queryset()
        total = len(simulations)
        success = 0
        failed = 0
        failed_list = list()

        for simulation in simulations:
            sim_name = simulation.name
            virl_ip = simulation.virl_host.ip_address

            simEngine = SimEngine(VIRL_USERNAME, VIRL_PASSWORD, virl_ip, sim_name)

            try:
                response = simEngine.stop()
            except:
                failed += 1
                failed_list.append((sim_name, virl_ip, "NON-RESPONSIVE"))
                continue

            if response.status_code == 200:  # stop was successful
                self.perform_destroy(simulation)
                success += 1
                continue


            elif response.status_code == 400:
                error_json = response.json()
                error = {'error': error_json['cause'], 'detail': error_json['details']}
                failed += 1
                failed_list.append((sim_name, virl_ip, error))
                continue

            elif response.status_code == 401:
                error_json = response.json()
                error = {'error': error_json['cause'], 'detail': error_json['details']}
                failed += 1
                failed_list.append((sim_name, virl_ip, error))
                continue

            elif response.status_code == 404:
                # simulation not found on server so we should delete from database
                self.perform_destroy(simulation)
                error_json = response.json()
                error = {'error': error_json['cause'], 'detail': "SIM not Found ==> Sanitation Mode"}
                continue

            else:
                error = { 'error': 'Unknown Error', 'detail': 'I couldn;t stop the simulation'}
                failed += 1
                failed_list.append((sim_name, virl_ip, error))
                continue

        return Response({"detail": "Done! Failed Stops: {}, Successful Stops: {}".format(failed, success)},  status=status.HTTP_200_OK)


    def perform_destroy(self, instance):
        simulation = instance
        user = simulation.user
        virl_host = simulation.virl_host

        virl_host.users.remove(user)
        # virl_host.current_lab = None
        virl_host.simulation.remove(simulation)
        virl_host.busy = False
        virl_host.usage -= 1
        virl_host.save()

        instance.delete()
        return


class SimulationNodesLinks(RetrieveAPIView):

    queryset = Simulation.objects.all()
    serializer_class = SimulationSerializer
    permission_classes = (IsAdminOrIsOwner,)
    lookup_field = "name"

    def retrieve(self, request, *args, **kwargs):
        simulation = self.get_object()
        sim_name = simulation.name
        user = request.user
        virl_ip = simulation.virl_host.ip_address
        mode = request.GET.get("mode", None)
        port = request.GET.get("port", None)

        simEngine = SimEngine(VIRL_USERNAME, VIRL_PASSWORD, virl_ip, sim_name)

        try:
            if (port == None) :
                response = simEngine.nodes_links(mode=mode)
            else:
                response = simEngine.nodes_links(mode=mode, port=port)
        except:
            error = {"error": "Error encountered accessing  your simulation nodes",
                     "detail": "NO RESPONSE! from the VIRL server. The Server IP may not be reachable"}
            return Response(error, status=status.HTTP_504_GATEWAY_TIMEOUT)

        if response.status_code == 200:  # launch was successful
            nodes = response.json()
            if "~mgmt-lxc" in nodes:
                del nodes["~mgmt-lxc"]
            return Response(nodes, status=status.HTTP_200_OK)

        elif response.status_code == 401:
            error_json = response.json()
            error = {'error': error_json['cause'], 'detail': error_json['details']}
            return Response(error, status=status.HTTP_403_FORBIDDEN)

        elif response.status_code == 404:
            # simulation not found on server so we should delete from database
            simulation = self.get_object()
            perform_sanitization(simulation)

            error_json = response.json()
            error = {'error': error_json['cause'], 'detail': "i couldn't find you on server, but performed sanitization"}
            return Response(error, status=status.HTTP_404_NOT_FOUND)

        elif response.status_code == 503:
            error_json = response.json()
            error = {'error': error_json['cause'], 'detail': error_json['details']}
            return Response(error, status=status.HTTP_403_FORBIDDEN)

        else:
            error = {'error': 'Unknown Error', 'detail': 'I could not retreive your simulation data'}
            return Response(error, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



class SimulationNodes(RetrieveAPIView):

    queryset = Simulation.objects.all()
    serializer_class = SimulationSerializer
    permission_classes = (IsAdminOrIsOwner,)
    lookup_field = "name"

    def retrieve(self, request, *args, **kwargs):
        simulation = self.get_object()
        sim_name = simulation.name
        user = request.user
        virl_ip = simulation.virl_host.ip_address

        simEngine = SimEngine(VIRL_USERNAME, VIRL_PASSWORD, virl_ip, sim_name)

        try:
            response = simEngine.nodes()

        except:
            error = {"error": "Error encountered accessing  your simulation nodes",
                     "detail": "NO RESPONSE! from the VIRL server. The Server IP may not be reachable"}
            return Response(error, status=status.HTTP_504_GATEWAY_TIMEOUT)

        if response.status_code == 200:  # launch was successful
            nodes = response.json()[sim_name]
            if "~mgmt-lxc" in nodes:
                del nodes["~mgmt-lxc"]
            return Response(nodes, status=status.HTTP_200_OK)

        elif response.status_code == 401:
            error_json = response.json()
            error = {'error': error_json['cause'], 'detail': error_json['details']}
            return Response(error, status=status.HTTP_403_FORBIDDEN)

        elif response.status_code == 404:
            # simulation not found on server so we should delete from database
            simulation = self.get_object()
            perform_sanitization(simulation)

            error_json = response.json()
            error = {'error': error_json['cause'], 'detail': "i couldn't find you on server, but performed sanitization"}
            return Response(error, status=status.HTTP_404_NOT_FOUND)


        elif response.status_code == 503:
            error_json = response.json()
            error = {'error': error_json['cause'], 'detail': error_json['details']}
            return Response(error, status=status.HTTP_403_FORBIDDEN)

        else:
            error = {'error': 'Unknown Error', 'detail': 'I could not retreive your simulation data'}
            return Response(error, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class SimulationNodesStartStop(RetrieveUpdateAPIView):
    queryset = Simulation.objects.all()
    serializer_class = SimulationSerializer
    permission_classes = (IsAdminOrIsOwner,)
    lookup_field = "name"

    def retrieve(self, request, *args, **kwargs):
        simulation = self.get_object()
        sim_name = simulation.name
        nodes = kwargs.get('nodes')
        user = request.user
        operation = kwargs.get('operation')
        virl_ip = simulation.virl_host.ip_address

        simEngine = SimEngine(VIRL_USERNAME, VIRL_PASSWORD, virl_ip, sim_name)

        try:
            if operation == 'start':
                response = simEngine.nodesStartStop(operation='start', nodes=[nodes])
            else:
                response = simEngine.nodesStartStop(operation='stop', nodes=[nodes])

        except:
            error = {"error": "Error encountered accessing  your simulation nodes",
                     "detail": "NO RESPONSE! from the VIRL server. The Server IP may not be reachable"}
            return Response(error, status=status.HTTP_504_GATEWAY_TIMEOUT)

        if response.status_code == 200:  # launch was successful
            msg = response.json()
            return Response(msg, status=status.HTTP_200_OK)

        elif response.status_code == 401:
            error_json = response.json()
            error = {'error': error_json['cause'], 'detail': error_json['details']}
            return Response(error, status=status.HTTP_403_FORBIDDEN)

        elif response.status_code == 404:
            # simulation not found on server so we should delete from database
            simulation = self.get_object()
            perform_sanitization(simulation)

            error_json = response.json()
            error = {'error': error_json['cause'], 'detail': "i couldn't find you on server, but performed sanitization"}
            return Response(error, status=status.HTTP_404_NOT_FOUND)


        elif response.status_code == 409:
            error_json = response.json()
            error = {'error': error_json['cause'], 'detail': error_json['details']}
            return Response(error, status=status.HTTP_403_FORBIDDEN)

        else:
            error = {'error': 'Unknown Error', 'detail': 'I could not retreive your simulation data'}
            return Response(error, status=status.HTTP_500_INTERNAL_SERVER_ERROR)




class SimulationLogs(RetrieveAPIView):

    queryset = Simulation.objects.all()
    serializer_class = SimulationSerializer
    permission_classes = (IsAdminOrIsOwner,)
    lookup_field = "name"

    def retrieve(self, request, *args, **kwargs):
        simulation = self.get_object()
        sim_name = simulation.name
        user = request.user
        virl_ip = simulation.virl_host.ip_address

        simEngine = SimEngine(VIRL_USERNAME, VIRL_PASSWORD, virl_ip, sim_name)

        try:
            response = simEngine.messages()
        except:
            error = {"error": "Error encountered while accessing your simulation nodes",
                     "detail": "NO RESPONSE! from the VIRL server. The Server IP may not be reachable"}
            return Response(error, status=status.HTTP_504_GATEWAY_TIMEOUT)

        if response.status_code == 200:  # launch was successful
            msgs = response.json()

            return Response(msgs, status=status.HTTP_200_OK)

        elif response.status_code == 401:
            error_json = response.json()
            error = {'error': error_json['cause'], 'detail': error_json['details']}
            return Response(error, status=status.HTTP_403_FORBIDDEN)

        elif response.status_code == 404:
            # simulation not found on server so we should delete from database
            simulation = self.get_object()
            perform_sanitization(simulation)

            error_json = response.json()
            error = {'error': error_json['cause'], 'detail': "Performed sanitization"}
            return Response(error, status=status.HTTP_404_NOT_FOUND)

        elif response.status_code == 503:
            error_json = response.json()
            error = {'error': error_json['cause'], 'detail': error_json['details']}
            return Response(error, status=status.HTTP_403_FORBIDDEN)

        else:
            error = {'error': 'Unknown Error', 'detail': 'I could not retrieve simulation data(Logs)'}
            return Response(error, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



class SimulationInterfaces(RetrieveAPIView):

    queryset = Simulation.objects.all()
    serializer_class = SimulationSerializer
    permission_classes = (IsAdminOrIsOwner,)
    lookup_field = "name"

    def retrieve(self, request, *args, **kwargs):
        simulation = self.get_object()
        sim_name = simulation.name
        user = request.user
        virl_ip = simulation.virl_host.ip_address

        simEngine = SimEngine(VIRL_USERNAME, VIRL_PASSWORD, virl_ip, sim_name)

        try:
            response = simEngine.interfaces()
        except:
            error = {"error": "Error encountered while accessing your simulation interfaces",
                     "detail": "NO RESPONSE! from the VIRL server. The Server IP may not be reachable"}
            return Response(error, status=status.HTTP_504_GATEWAY_TIMEOUT)

        if response.status_code == 200:  # launch was successful
            interfaces = response.json()[sim_name]
            if "~mgmt-lxc" in interfaces:
                del interfaces["~mgmt-lxc"]

            return Response(interfaces, status=status.HTTP_200_OK)

        elif response.status_code == 401:
            error_json = response.json()
            error = {'error': error_json['cause'], 'detail': error_json['details']}
            return Response(error, status=status.HTTP_403_FORBIDDEN)

        elif response.status_code == 404:
            # simulation not found on server so we should delete from database
            simulation = self.get_object()
            perform_sanitization(simulation)

            error_json = response.json()
            error = {'error': error_json['cause'],
                     'detail': "i couldn't find you on server, but performed sanitization"}
            return Response(error, status=status.HTTP_404_NOT_FOUND)

        else:
            error = {'error': 'Unknown Error', 'detail': 'I could not retrieve simulation interfaces'}
            return Response(error, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class SimulationCaptureList(ListCreateAPIView):
    queryset = Simulation.objects.all()
    serializer_class = SimulationSerializer
    permission_classes = (IsAdminOrIsOwner,)
    lookup_field = "name"

    def list(self, request, *args, **kwargs):
        simulation = self.get_object()
        sim_name = simulation.name
        user = request.user
        virl_ip = simulation.virl_host.ip_address

        simEngine = SimEngine(VIRL_USERNAME, VIRL_PASSWORD, virl_ip, sim_name)

        try:
            response = simEngine.list_captures()
        except:
            error = {"error": "Error encountered while fetching your traffic captures",
                     "detail": "NO RESPONSE! from the VIRL server. The Server IP may not be reachable"}
            return Response(error, status=status.HTTP_504_GATEWAY_TIMEOUT)

        if response.status_code == 200:  # launch was successful
            msgs = response.json()

            return Response(msgs, status=status.HTTP_200_OK)

        elif response.status_code == 401:
            error_json = response.json()
            error = {'error': error_json['cause'], 'detail': error_json['details']}
            return Response(error, status=status.HTTP_403_FORBIDDEN)

        elif response.status_code == 404:

            # simulation not found on server so we should delete from database
            # simulation = self.get_object()
            # perform_sanitization(simulation)

            error_json = response.json()
            error = {'error': error_json['cause'],
                     'details': "i couldn't find you on server, but performed sanitization"}
            return Response(error, status=status.HTTP_404_NOT_FOUND)

        else:
            error = {'error': 'Unknown Error', 'detail': 'I could not retrieve your traffic captures list'}
            return Response(error, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def create(self, request, *args, **kwargs):
        simulation = self.get_object()
        sim_name = simulation.name
        virl_ip = simulation.virl_host.ip_address

        node = request.data.get("node")
        interface = request.data.get("interface")
        pcap_filter = request.data.get("pcap-filter")


        simEngine = SimEngine(VIRL_USERNAME, VIRL_PASSWORD, virl_ip, sim_name)

        try:
            response = simEngine.create_capture(node=node, interface=interface, pcap_filter=pcap_filter)
        except:
            error = {"error": "Error encountered while creating your traffic capture",
                     "detail": "NO RESPONSE! from the VIRL server. The Server IP may not be reachable"}
            return Response(error, status=status.HTTP_504_GATEWAY_TIMEOUT)

        if response.status_code == 200:  # launch was successful
            msgs = response.json()

            return Response(msgs, status=status.HTTP_200_OK)

        elif response.status_code == 401:
            error_json = response.json()
            error = {'error': error_json['cause'], 'detail': error_json['details']}
            return Response(error, status=status.HTTP_403_FORBIDDEN)

        elif response.status_code == 404:

            # simulation not found on server so we should delete from database
            # simulation = self.get_object()
            # perform_sanitization(simulation)

            error_json = response.json()
            error = {'error': error_json['cause'],
                     'details': "i couldn't find you on server, but performed sanitization"}
            return Response(error, status=status.HTTP_404_NOT_FOUND)

        else:
            error = {'error': 'Unknown Error', 'detail': 'Error encountered creating traffic capture'}
            return Response(error, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class SimulationCaptureDetail(RetrieveDestroyAPIView):
    queryset = Simulation.objects.all()
    serializer_class = SimulationSerializer
    permission_classes = (IsAdminOrIsOwner,)
    lookup_field = "name"


    def retrieve(self, request, *args, **kwargs):
        simulation = self.get_object()
        sim_name = simulation.name
        cap_name = kwargs.get('cap_name')
        user = request.user
        virl_ip = simulation.virl_host.ip_address

        simEngine = SimEngine(VIRL_USERNAME, VIRL_PASSWORD, virl_ip, sim_name)

        try:
            response = simEngine.retrieve_capture(cap_name)
        except:
            error = {"error": "Error encountered while retreiving your traffic capture",
                     "detail": "NO RESPONSE! from the VIRL server. The Server IP may not be reachable"}
            return Response(error, status=status.HTTP_504_GATEWAY_TIMEOUT)

        if response.status_code == 200:  # launch was successful
            msgs = response
            response = HttpResponse(msgs, content_type='application/vnd.tcpdump.pcap')
            response['Content-Disposition'] = 'attachment; filename="{0}.pcap"'.format(cap_name)
            # response.status = status.HTTP_200_OK
            return response

        elif response.status_code == 401:
            error_json = response.json()
            error = {'error': error_json['cause'], 'detail': error_json['details']}
            return Response(error, status=status.HTTP_403_FORBIDDEN)

        elif response.status_code == 404:

            # simulation not found on server so we should delete from database
            # simulation = self.get_object()
            # perform_sanitization(simulation)

            error_json = response.json()
            error = {'error': error_json['cause'],
                     'detail': "i couldn't find the capture on server, but performed sanitization"}
            return Response(error, status=status.HTTP_404_NOT_FOUND)

        else:
            error = {'error': 'Unknown Error', 'detail': 'I could not retrieve your traffic capture'}
            return Response(error, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



    def delete(self, request, *args, **kwargs):
        simulation = self.get_object()
        sim_name = simulation.name
        cap_name = kwargs.get('cap_name')
        virl_ip = simulation.virl_host.ip_address

        simEngine = SimEngine(VIRL_USERNAME, VIRL_PASSWORD, virl_ip, sim_name)

        try:
            response = simEngine.delete_capture(cap_name)
        except:
            error = {"error": "Error encountered while deleting your traffic capture",
                     "detail": "NO RESPONSE! from the VIRL server. The Server IP may not be reachable"}
            return Response(error, status=status.HTTP_504_GATEWAY_TIMEOUT)

        if response.status_code == 200: #delete successful
            msg = response.json()
            # response.status = status.HTTP_200_OK
            return Response(msg, status=status.HTTP_204_NO_CONTENT)

        elif response.status_code == 401:
            error_json = response.json()
            error = {'error': error_json['cause'], 'detail': error_json['details']}
            return Response(error, status=status.HTTP_403_FORBIDDEN)

        elif response.status_code == 404:

            # simulation not found on server so we should delete from database
            #simulation = self.get_object()
            #perform_sanitization(simulation)

            error_json = response.json()
            error = {'error': error_json['cause'],
                     'detail': "i couldn't find the capture on server, but performed sanitization"}
            return Response(error, status=status.HTTP_404_NOT_FOUND)

        else:
            error = {'error': 'Unknown Error', 'detail': 'I could not delete your traffic capture'}
            return Response(error, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class SimulationAllLabData(ListAPIView):

    serializer_class = SimulationSerializer
    permission_classes = (IsAdminOrIsOwner,)

    def get_queryset(self):
        lab = self.kwargs.get('lab', None)
        return Simulation.objects.all().filter(lab__code=lab)


    def list(self, request, *args, **kwargs):
        all_data = []
        success_results = []
        error_results = []
        node_connection_success = 0
        node_connection_errors = 0

        request.GET._mutable = True # to make the request obj mutable to add a new key.
        request.GET['mode'] = 'telnet'

        for simulation in self.get_queryset():
            data = {}
            sim_name = simulation.name


            request.GET['port'] = '1' # to get monitor line
            nodesMonitorLinkResponse = SimulationNodesLinks.as_view()(request,name=sim_name)
            nodesMonitorLinkData = nodesMonitorLinkResponse.data

            request.GET['port'] = '0' # to get console line
            nodesConsoleLinkResponse = SimulationNodesLinks.as_view()(request, name=sim_name)
            nodesConsoleLinkData = nodesConsoleLinkResponse.data

            if nodesMonitorLinkResponse.status_code and nodesConsoleLinkResponse.status_code == 200:
                node_connection_success += 1
                data['user'] = simulation.user.username
                data['user_fullname'] = simulation.user.get_full_name()
                data['lab'] = simulation.lab.code
                data['name'] = sim_name
                data['virl_host'] = simulation.virl_host.ip_address
                data['timestamp'] = simulation.timestamp
                data['nodes_monitor_line'] = nodesMonitorLinkData
                data['nodes_console_line'] = nodesConsoleLinkData

                success_results.append(data)
            else:
                node_connection_errors += 1
                data['user'] = simulation.user.username
                data['user_fullname'] = simulation.user.get_full_name()
                data['lab'] = simulation.lab.code
                data['name'] = sim_name
                data['virl_host'] = simulation.virl_host.ip_address
                data['timestamp'] = simulation.timestamp
                data['nodes_monitor_line'] = nodesMonitorLinkData
                data['nodes_console_line'] = nodesConsoleLinkData

                error_results.append(data)

        request.GET._mutable = False # to make request obj un-mutable again

        all_data.append({'success_counts':node_connection_success, 'error_counts':node_connection_errors,})
        all_data.append({'success_results':success_results, 'error_results':error_results})

        return Response(all_data, status=status.HTTP_200_OK)

class SimulationUserLabData(RetrieveAPIView):

    queryset = Simulation.objects.all()
    serializer_class = SimulationSerializer
    permission_classes = (IsAdminOrIsOwner,)
    lookup_field = 'user__username'

    def get_object(self):
        filter_kwargs = {'user__username': self.kwargs['user'], 'lab__code':self.kwargs['lab']}
        obj =  get_object_or_404(self.queryset, **filter_kwargs)
        self.check_object_permissions(self.request, obj)
        return obj

    def retrieve(self, request, *args, **kwargs):
        all_data = {}
        node_connection_success = 0
        node_connection_errors = 0

        simulation = self.get_object()
        success_data = {}
        error_data = {}
        sim_name = simulation.name
        request.GET._mutable = True
        request.GET['mode'] = 'telnet'

        request.GET['port'] = '1'  # to get monitor line
        nodesMonitorLinkResponse = SimulationNodesLinks.as_view()(request, name=sim_name)
        nodesMonitorLinkData = nodesMonitorLinkResponse.data

        request.GET['port'] = '0'  # to get console line
        nodesConsoleLinkResponse = SimulationNodesLinks.as_view()(request, name=sim_name)
        nodesConsoleLinkData = nodesConsoleLinkResponse.data

        nodesInterfacesResponse = SimulationInterfaces.as_view()(request, name=sim_name)
        nodesInterfacesData = nodesInterfacesResponse.data

        request.GET._mutable = False


        nodesMgmtInterfaces = {}

        for nodeName, interfaceName in nodesInterfacesData.items():
            if 'management' in interfaceName:
                if interfaceName['management']['network'] == 'flat':
                    nodesMgmtInterfaces[nodeName] = interfaceName['management']['ip-address']
                else:
                    nodesMgmtInterfaces[nodeName] = ""



        if nodesMonitorLinkResponse.status_code ==200 \
                and nodesInterfacesResponse.status_code == 200\
                and nodesConsoleLinkResponse.status_code == 200:
            node_connection_success += 1
            success_data['user'] = simulation.user.username
            success_data['user_fullname'] = simulation.user.get_full_name()
            success_data['lab'] = simulation.lab.code
            success_data['name'] = sim_name
            success_data['virl_host'] = simulation.virl_host.ip_address
            success_data['timestamp'] = simulation.timestamp
            success_data['nodes_mgmt_interface'] = nodesMgmtInterfaces
            success_data['nodes_monitor_line'] = nodesMonitorLinkData
            success_data['nodes_console_line'] = nodesConsoleLinkData

        else:
            node_connection_errors += 1
            error_data['user'] = simulation.user.username
            error_data['user_fullname'] = simulation.user.get_full_name()
            error_data['lab'] = simulation.lab.code
            error_data['name'] = sim_name
            error_data['virl_host'] = simulation.virl_host.ip_address
            error_data['timestamp'] = simulation.timestamp
            success_data['nodes_monitor_line'] = nodesMonitorLinkData
            success_data['nodes_mgmt_interface'] = nodesMgmtInterfaces

        all_data['success_result'] = success_data
        all_data['error_result'] = error_data

        return Response(all_data, status=status.HTTP_200_OK)


# class SimulationUserLabData(RetrieveAPIView):
#
#     queryset = Simulation.objects.all()
#     serializer_class = SimulationSerializer
#     permission_classes = (IsAdminOrIsOwner,)
#     lookup_field = 'user__username'
#
#     def get_object(self):
#         filter_kwargs = {'user__username': self.kwargs['user'], 'lab__code':self.kwargs['lab']}
#         obj =  get_object_or_404(self.queryset, **filter_kwargs)
#         self.check_object_permissions(self.request, obj)
#         return obj
#
#     def retrieve(self, request, *args, **kwargs):
#         all_data = {}
#         node_connection_success = 0
#         node_connection_errors = 0
#
#         simulation = self.get_object()
#         success_data = {}
#         error_data = {}
#         sim_name = simulation.name
#         request.GET._mutable = True
#         request.GET['mode'] = 'telnet'
#
#         request.GET['port'] = '1'  # to get monitor line
#         nodesMonitorLinkResponse = SimulationNodesLinks.as_view()(request, name=sim_name)
#         nodesMonitorLinkData = nodesMonitorLinkResponse.data
#
#         request.GET['port'] = '0'  # to get console line
#         nodesConsoleLinkResponse = SimulationNodesLinks.as_view()(request, name=sim_name)
#         nodesConsoleLinkData = nodesConsoleLinkResponse.data
#
#         request.GET._mutable = False
#
#         if nodesMonitorLinkResponse.status_code and nodesConsoleLinkResponse.status_code == 200:
#             node_connection_success += 1
#             success_data['user'] = simulation.user.username
#             success_data['user_fullname'] = simulation.user.get_full_name()
#             success_data['lab'] = simulation.lab.code
#             success_data['name'] = sim_name
#             success_data['virl_host'] = simulation.virl_host.ip_address
#             success_data['timestamp'] = simulation.timestamp
#             success_data['nodes_monitor_line'] = nodesMonitorLinkData
#             success_data['nodes_console_line'] = nodesConsoleLinkData
#         else:
#             node_connection_errors += 1
#             error_data['user'] = simulation.user.username
#             error_data['user_fullname'] = simulation.user.get_full_name()
#             error_data['lab'] = simulation.lab.code
#             error_data['name'] = sim_name
#             error_data['virl_host'] = simulation.virl_host.ip_address
#             error_data['timestamp'] = simulation.timestamp
#             error_data['nodes_monitor_line'] = nodesMonitorLinkData
#             error_data['nodes_console_line'] = nodesConsoleLinkData
#
#         all_data['success_result'] = success_data
#         all_data['error_result'] = error_data
#
#         return Response(all_data, status=status.HTTP_200_OK)

