import os
from django.conf import settings
from django.shortcuts import render
from django.views.generic.base import TemplateView
from .models import VirlServer, Course, Lab
from simEngine.models import SimEngine
from data import VIRL_USERNAME, VIRL_PASSWORD
import requests
from requests.auth import HTTPBasicAuth
from django.views.generic.detail import DetailView




class OspfLab(TemplateView):
    template_name = "topo-status.html"

    def virl_get(self, virl_ip, append_url="", **params):
        auth = HTTPBasicAuth(VIRL_USERNAME, VIRL_PASSWORD)
        url = "http://%s:19399/%s" % (virl_ip, append_url)
        params = params
        response = requests.get(url, auth=auth, params=params)
        print
        "URL: %s <<>> Status: %s " % (response.url, response.status_code)
        return response

    def virl_stop(self, virl_ip, sim_id=None):
        if not sim_id:
            sim_id = self.sim_file.split('.')[0]
        response = self.virl_get(virl_ip, append_url="simengine/rest/stop/%s" % (sim_id))
        return response

    def post(self, request, *args, **kwargs):
        context = self.get_context_data()
        user = request.user
        print
        request.POST.get("operation")

        if request.POST.get("operation") == "stop":
            lab = request.POST.get("lab")
            print
            "this is lab", lab
            if VirlServer.objects.filter(assigned_to=user).exists():
                virl_server = VirlServer.objects.get(assigned_to=user)
                virl_server_ip = str(virl_server.ip_address)
                virl_username = VIRL_USERNAME
                virl_pasword = VIRL_PASSWORD

                response = self.virl_stop(virl_server_ip, sim_id=lab)
                print
                "response here: ", response.status_code
                if response.status_code == 200:  # stop was successful
                    context['lab_status'] = "Simulation was successfully stopped."
                    virl_server.assigned_to = None
                    virl_server.current_lab = None
                    virl_server.save()
                elif response.status_code == 404:
                    context['lab_status'] = "No simulation was found "
                elif response.status_code == 401:
                    context['lab_status'] = "Authentication Failed"
                else:
                    context['lab_status'] = "Couldnt not stop: Unknown Error"
            else:
                context['lab_status'] = "No simulation found!"
            return self.render_to_response(context)
        else:
            # check if user is assigned to any server
            lab = request.POST.get("lab")

            if not VirlServer.objects.filter(assigned_to=user).exists():

                # get an available viral server
                if VirlServer.objects.filter(assigned_to=None).exists():
                    virl_server = VirlServer.objects.random()  # returns a random un-assigned server
                    virl_server_ip = str(virl_server.ip_address)
                    virl_username = VIRL_USERNAME
                    virl_pasword = VIRL_PASSWORD
                    virl_file = lab + ".virl"

                    engine = SimEngine(virl_username, virl_pasword, virl_server_ip, 'challenge-lab.virl')
                    print(virl_username, virl_pasword, virl_server_ip, virl_file)
                    try:
                        response = engine.launch()
                        print
                        "response: ", response.status_code
                        if response.status_code == 200:  # launch was successful
                            context['lab_status'] = "Your Simulation launch was successful"
                            try:
                                server_in_use = VirlServer.objects.get(ip_address=virl_server_ip)
                                lab = Lab.objects.get(tag=lab)
                                print
                                "server: ", server_in_use
                                server_in_use.assigned_to = user
                                server_in_use.current_lab = lab
                                server_in_use.save()
                                context[
                                    "assign_message"] = "You've been assigned a server, check dashboard for more info"
                                return self.render_to_response(context)
                            except:
                                context["assign_message"] = "Server assignment failed!!!"

                    except:
                        context['lab_status'] = "Simulation launch failed! "

                else:
                    context["assign_message"] = "Simulation could not be started because no server was available"
            else:
                context["assign_message"] = "You already have a running lab session, please stop and try again"

            return self.render_to_response(context)


class TopoData(TemplateView):
    template_name = "topo-data.html"

    def get_context_data(self, **kwargs):
        context = super(TopoData, self).get_context_data(**kwargs)
        user = self.request.user
        try:
            server = VirlServer.objects.get(assigned_to=user)
            context["lab"] = str(server.current_lab.tag)
            context['server_ip'] = str(server.ip_address)
        except:
            context['server_ip'] = None
        return context


class CourseLabs(DetailView):
    model = Course
    template_name = "course-labs.html"
    context_object_name = "course"

    slug_url_kwarg = "code"

    def get_slug_field(self):
        self.slug_field = "code"
        return self.slug_field


