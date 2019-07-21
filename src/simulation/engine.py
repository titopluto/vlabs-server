import json
import requests
import os
from requests.auth import HTTPBasicAuth
import collections
from .constants import MEDIA_PATH

def convert(data):
    if isinstance(data, collections.basestring):
        return str(data)
    elif isinstance(data, collections.Mapping):
        return dict(map(convert, data.iteritems()))
    elif isinstance(data, collections.Iterable):
        return type(data)(map(convert, data))
    else:
        return data


class SimEngine():

    def __init__(self, username, password, virl_ip, sim_name, sim_file=None, timeout=(5, 10),**kwargs):
        self.username = username.strip()
        self.password = password.strip()
        self.virl_ip = virl_ip.strip()
        self.sim_name = sim_name.strip()
        self.sim_file = sim_file
        self.timeout = timeout
        self.api_sim_file = kwargs.get('api_sim_file', None)

    def get(self, append_url="", **params):
        auth = HTTPBasicAuth(self.username, self.password)
        url = "http://%s:19399/%s" % (self.virl_ip, append_url)
        params = params
        headers = {"Content-Type": "application/json"}
        response = requests.get(url, auth=auth, headers=headers, params=params, timeout=self.timeout)
        print("URL: {} <<>> Status: {}".format(response.url, response.status_code))
        return response

    def post(self, append_url="", **params):
        auth = HTTPBasicAuth(self.username, self.password)
        url = "http://%s:19399/%s" % (self.virl_ip, append_url)
        params = params
        response = requests.post(url, auth=auth, params=params, timeout=self.timeout)
        print("URL: %s <<>> Status: %s" % (response.url, response.status_code))
        return response

    def put(self, append_url="", **params):
        auth = HTTPBasicAuth(self.username, self.password)
        url = "http://%s:19399/%s" % (self.virl_ip, append_url)
        params = params
        response = requests.put(url, auth=auth, params=params, timeout=self.timeout)
        print("URL: %s <<>> Status: %s" % (response.url, response.status_code))
        return response

    def launch(self, expiry):
        dir_path = MEDIA_PATH

        if not self.api_sim_file:
            file_path = os.path.join(dir_path, self.sim_file)
            data = open(file_path, 'rb').read()
        else:
            file_path = self.api_sim_file
            data = file_path

        auth = HTTPBasicAuth(self.username, self.password)
        url = "http://%s:19399/simengine/rest/launch" % (self.virl_ip)
        params = {'session': self.sim_name, 'expires':expiry}
        #
        
        headers = {'Content-Type': 'text/xml',
                   'charset': 'UTF-8'}
        response = requests.post(url, auth=auth, headers=headers, data=data, params=params, timeout=self.timeout)
        print("Response_at_launch", response.url, response.status_code, sep="\t")
        return response

    def confirm_simulation(self):
        response = self.get(append_url="simengine/rest/status/%s" % (self.sim_name))
        return response

    def stop(self):
        response = self.get(append_url="simengine/rest/stop/%s" % (self.sim_name))
        return response

    def messages(self):
        response = self.get(append_url="/simengine/rest/events/{0}".format(self.sim_name))
        return response

    def nodes_links(self, mode, port=0):
        response = self.get(append_url="simengine/rest/serial_port/%s" % (self.sim_name), mode=mode, port=port )

        return response

    def nodes(self):
        response = self.get(append_url="simengine/rest/nodes/%s" % (self.sim_name))
        print ("NODE+R", response)
        return response

    def nodesStartStop(self, operation, nodes):
        if operation == 'start' :
            response = self.put(append_url="simengine/rest/update/%s/start" % (self.sim_name), nodes=nodes)
        else:
            response = self.put(append_url="simengine/rest/update/%s/stop" % (self.sim_name), nodes=nodes)
        return response


    def status(self):
        response = self.get(append_url='simengine/rest/status/{0}'.format(self.sim_name))
        return response


    def interfaces(self):
        response = self.get(append_url="simengine/rest/interfaces/%s" % (self.sim_name))
        return response

    def create_capture(self, node, interface, pcap_filter):
        auth = HTTPBasicAuth(self.username, self.password)
        append_url = "simengine/rest/capture/%s" % (self.sim_name)
        url = "http://%s:19399/%s" % (self.virl_ip, append_url)
        params = {"node":node, "interface":interface, "pcap-filter": pcap_filter}

        response = requests.post(url, auth=auth, params=params, timeout=self.timeout)
        return response


    def list_captures(self):
        response = self.get(append_url="simengine/rest/capture/%s" % (self.sim_name))
        return response

    def retrieve_capture(self, cap_name):
        auth = HTTPBasicAuth(self.username, self.password)
        append_url = "simengine/rest/capture/%s" % (self.sim_name)
        url = "http://%s:19399/%s" % (self.virl_ip, append_url)
        headers = {"Accept": "application/vnd.tcpdump.pcap"}
        params = {"capture": cap_name}
        response = requests.get(url, auth=auth, headers=headers, params=params, timeout=self.timeout)
        return response

    def delete_capture(self, cap_name):
        auth = HTTPBasicAuth(self.username, self.password)
        append_url = "simengine/rest/capture/%s" % (self.sim_name)
        url = "http://%s:19399/%s" % (self.virl_ip, append_url)
        headers = {"Accept": "application/vnd.tcpdump.pcap"}
        params = {"capture": cap_name}
        response = requests.delete(url, auth=auth, headers=headers, params=params, timeout=self.timeout)
        return response



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

    def validate_virl_file(self, expiry):
        dir_path = MEDIA_PATH
        file_path = os.path.join(dir_path, self.sim_file)
        auth = HTTPBasicAuth(self.username, self.password)
        url = "http://%s:19399/simengine/rest/launch" % (self.virl_ip)
        params = {'session': self.sim_name, 'expires':expiry}
        data = open(file_path, 'rb').read()
        headers = {'Content-Type': 'text/xml',
                   'charset': 'UTF-8'}
        response = requests.post(url, auth=auth, headers=headers, data=data, params=params, timeout=self.timeout)
        print("Response_at_launch", response.url, response.status_code, sep="\t")
        return response



    def snapshot(self, node_id, append_url=''):
        response = convert(
            self.post(append_url="simengine/rest/snapshot/%s/%s" % (self.sim_name, node_id), name=node_id).json())
        return

    def tracking(self, sim_id=None):
        if not sim_id:
            sim_id = self.sim_file.split('.')[0]
        response = convert(
            self.post(append_url="simengine/rest/tracking", session_id=sim_id, topics="event.nodes").json())
        return response


# from src.tests import *
# sim = SimEngine("guest", "!Nt3rn3t!Nt3rn3t", "10.0.132.103", 'ospf_lab.virl')
# sim2 = SimEngine("user0", "Meilab123", "10.0.132.103", 'ospf_lab.virl')

# sim = SimEngine('guest', 'Meilab123', '10.0.132.51', 'inwk6312Lab-inwkadmin')

# sim2.launch()
# print
# sim.telnet_nodes()
# print
# sim2.telnet_nodes()
# print
# sim2.stop()
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





