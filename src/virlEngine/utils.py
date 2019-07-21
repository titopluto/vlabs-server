import json
import requests
import os
from requests.auth import HTTPBasicAuth
from .helper import convert


class SimEngine():
    def __init__(self, username, password, virl_ip, sim_file=None):
        self.username = username
        self.password = password
        self.virl_ip = virl_ip
        self.sim_file = sim_file

    def get(self, append_url="", **params):
        auth = HTTPBasicAuth(self.username, self.password)
        url = "http://%s:19399/%s" % (self.virl_ip, append_url)
        params = params
        response = requests.get(url, auth=auth, params=params)
        print
        "URL: %s <<>> Status: %s " % (response.url, response.status_code)

        if response.status_code == 200:
            return response
        else:
            print
            response.status_code
            print
            response.raise_for_status()
            return

    def post(self, append_url="", **params):
        auth = HTTPBasicAuth(self.username, self.password)
        url = "http://%s:19399/%s" % (self.virl_ip, append_url)
        params = params
        response = requests.post(url, auth=auth, params=params)
        print
        "URL: %s <<>> Status: %s " % (response.url, response.status_code)

        if response.status_code == 200:
            return response
        else:
            print
            response.status_code
            print
            response.raise_for_status()
            return

    def launch(self, sim_file=None):
        if not sim_file:
            sim_file = self.sim_file
        dir_path = os.path.dirname(os.path.realpath(__file__))
        file_path = os.path.join(dir_path, sim_file)
        auth = HTTPBasicAuth(self.username, self.password)
        url = "http://%s:19399/simengine/rest/launch" % (self.virl_ip)
        params = {'session': sim_file.split(".")[0]}
        data = open(file_path, 'rb').read()
        headers = {'Content-Type': 'text/xml',
                   'charset': 'UTF-8'}
        response = requests.post(url, auth=auth, headers=headers, data=data, params=params)

        if response.status_code == 200:
            return response
        else:
            print
            response.status_code
            print
            response.raise_for_status()
            return

    def stop(self, sim_id=None):
        if not sim_id:
            sim_id = self.sim_file.split('.')[0]
        response = self.get(append_url="simengine/rest/stop/%s" % (sim_id))
        return response

    def telnet_nodes(self, sim_id=None):
        if not sim_id:
            sim_id = self.sim_file.split('.')[0]
        nodes = convert(self.get(append_url="simengine/rest/serial_port/%s" % (sim_id), mode="telnet").json())
        if "~mgmt-lxc" in nodes:
            del nodes["~mgmt-lxc"]
        return nodes

    def get_nodes(self, append_url='', sim_id=None):
        if not sim_id:
            sim_id = self.sim_file.split('.')[0]
        response = convert(self.get(append_url="simengine/rest/nodes/%s" % (sim_id)).json())
        nodes = dict()
        for key, value in response[sim_id].iteritems():
            nodes[key] = value

        return nodes

    def get_links(self, append_url='', sim_id=None):
        if not sim_id:
            sim_id = self.sim_file.split('.')[0]
        response = convert(self.get(append_url="simengine/rest/link/%s" % (sim_id)).json())
        links = dict()
        for key, value in response.iteritems():
            links[key] = value

        return links

    def get_links_info(self, node_id, iface_id, append_url='', sim_id=None):
        if not sim_id:
            sim_id = self.sim_file.split('.')[0]
        response = convert(self.get(append_url="simengine/rest/link/%s/%s/%s" % (sim_id, node_id, iface_id)).json())
        links = dict()
        for key, value in response.iteritems():
            links[key] = value

        return links

    def interfaces(self, append_url='', sim_id=None):
        if not sim_id:
            sim_id = self.sim_file.split('.')[0]
        response = convert(self.get(append_url="simengine/rest/interfaces/%s" % (sim_id)).json())
        links = dict()
        for key, value in response[sim_id].iteritems():
            links[key] = value

        return links

    def snapshot(self, node_id, append_url='', sim_id=None):
        if not sim_id:
            sim_id = self.sim_file.split('.')[0]
        response = convert(
            self.post(append_url="simengine/rest/snapshot/%s/%s" % (sim_id, node_id), name=node_id).json())
        return

    def tracking(self, sim_id=None):
        if not sim_id:
            sim_id = self.sim_file.split('.')[0]
        response = convert(
            self.post(append_url="simengine/rest/tracking", session_id=sim_id, topics="event.nodes").json())
        return response


# from src.tests import *
sim = SimEngine("guest", "!Nt3rn3t!Nt3rn3t", "10.0.132.103", 'ospf_lab.virl')
sim2 = SimEngine("user0", "Meilab123", "10.0.132.103", 'ospf_lab.virl')

# sim2.launch()
print
sim.telnet_nodes()
print
sim2.telnet_nodes()
print
sim2.stop()
# print sim.get_links()
#
# print sim.get_links_info("R3", '1')
# print sim.snapshot("R2")
# print sim.tracking()
# print sim.get("simengine/rest/serial_port/ospf_lab", mode="telnet")
# print sim.interfaces()

# print dir(collections)

# print sim.interfaces("lab09.project.1-v0Ccn8")

# print sim.info('/simengine/rest/nodes/ospf_lab').text
# sim.stop()
# links = {}
# print sim.interfaces()['R3']['0']
# print sim.get_links_info("R3", '1')
# # print sim.snapshot("R2").text





