from django.conf.urls import url, include
from rest_framework_jwt.views import obtain_jwt_token, refresh_jwt_token, verify_jwt_token

from .views import UserList, UserDetail, UserSelfDetail

from .views import (LabList, LabDetail,)

from course.views import CourseVlabList, CourseLabVlabList, CourseDetail, CourseLabList, CourseByGroup

from virtualLab.views import VirtualLabDetail, VirtualLabList

from virlHost.views import VirlHostList, VirlHostDetailUpdate, VirlHostReadyList

from simulation.views import (SimulationList, SimulationRetrieveDestroy, SimulationDestroyALL, SimulationNodes,
                              SimulationNodesStartStop,SimulationNodesLinks, SimulationInterfaces,
                              SimulationCaptureList, SimulationCaptureDetail, SimulationLogs,
                              SimulationUserList,SimulationSelfList, SimulationCreate, SimulationRetrieveByID,
                              SimulationAllLabData, SimulationUserLabData, SimulationListUnique, SimulationNodesByLab
                              )

from cohort.views import CohortsListView




urlpatterns = [
    url(r'^auth/', include('rest_framework.urls', namespace='rest_framework')),

    # Authentication
    url(r'^api-token-auth/', obtain_jwt_token),
    url(r'^api-token-refresh/', refresh_jwt_token),
    url(r'^api-token-verify/', verify_jwt_token),

    url(r'^user/$', UserSelfDetail.as_view(), name="users-self-detail"),
    url(r'^users/$', UserList.as_view(), name="users-list"),
    url(r'^users/(?P<username>[\w.@+-]+)$', UserDetail.as_view(), name="users-detail"),
    
    #Courses
    url(r'^courses-lab/$', CourseLabList.as_view(), name="courses-lab-list"),
    url(r'^courses-vlab/$', CourseVlabList.as_view(), name="courses-vlab-list"),
    url(r'^courses-lab-vlab/$', CourseLabVlabList.as_view(), name="courses-lab-vlab-list"),
    url(r'^courses/(?P<code>[\w.@+-]+)$', CourseDetail.as_view(), name="courses-detail"),

    url(r'^courses-group/(?P<group>[\w.@+-]+)$', CourseByGroup.as_view(), name="courses-by-group"),
    #Labs
    url(r'^labs/$', LabList.as_view(), name="Labs-list"),
    url(r'^labs/(?P<code>[\w.@+-]+)$', LabDetail.as_view(), name="lab-detail"),

    #VIRL labs
    url(r'^vlabs/$', VirtualLabList.as_view(), name="vLabs-list"),
    url(r'^vlabs/(?P<code>[\w.@+-]+)$', VirtualLabDetail.as_view(), name="vlabs-detail"),

    #VIRL Servers
    url(r'^vhosts/$', VirlHostList.as_view(), name="vhosts-list"),
    url(r'^vhosts/ready/$', VirlHostReadyList.as_view(), name="vhosts-ready-list"),
    url(r'^vhosts/(?P<ip_address>[\w.@+-]+)$', VirlHostDetailUpdate.as_view(), name="vhosts-detail"),

    #Virl Servers ==> Update VIRL Server
    # url(r'^vhosts/(?P<ip_address>[\w.@+-]+)$', VirlHostUpdate.as_view(), name="vhosts-update"),

    #Simulation list
    url(r'^simulations/$', SimulationSelfList.as_view(), name="simulation-self"),
    url(r'^simulations/all$', SimulationList.as_view(), name="simulation-list"),
    url(r'^simulations/all/unique/lab$', SimulationListUnique.as_view(), name="simulation-list-unique"),
    url(r'^simulations/lab/(?P<lab>[\w.@+-]+)/nodes$', SimulationNodesByLab.as_view(), name="simulation-lab-nodes"),

    #Simuulation ==> Stopping all simulations
    url(r'^simulations/stop-all$', SimulationDestroyALL.as_view(), name="simulation-stop-all"),

    url(r'^simulations/id/(?P<name>[\w.@+-]+)$', SimulationRetrieveByID.as_view(), name="simulation-retreive-by-id"),
    url(r'^simulations/user/(?P<username>[\w.@+-]+)$', SimulationUserList.as_view(),name="simulation-user-list"),
    url(r'^simulations/create$', SimulationCreate.as_view(), name="simulation-create"),
    url(r'^simulations/create/(?P<user>[\w.@+-]+)$', SimulationCreate.as_view(), name="simulation-create"),

    url(r'^simulations/(?P<name>[\w.@+-]+)$', SimulationRetrieveDestroy.as_view(), name="simulation-detail-destroy"),

    url(r'^simulations/(?P<name>[\w.@+-]+)/nodes/$', SimulationNodes.as_view(), name="simulation-nodes"),

    url(r'^simulations/(?P<name>[\w.@+-]+)/nodes/(?P<operation>[\w.@+-]+)/(?P<nodes>[\w.@+-]+)$', SimulationNodesStartStop.as_view(),name="simulation-nodes-start-stop"),

    url(r'^simulations/(?P<name>[\w.@+-]+)/nodes_links$', SimulationNodesLinks.as_view(), name="simulation-nodes-links"),

    url(r'^simulations/(?P<name>[\w.@+-]+)/interfaces$', SimulationInterfaces.as_view(), name="simulation-interfaces"),

    url(r'^simulations/(?P<name>[\w.@+-]+)/captures/(?P<cap_name>[\w.@+-]+)$', SimulationCaptureDetail.as_view(),name="simulation-captures-detail"),

    url(r'^simulations/(?P<name>[\w.@+-]+)/captures$', SimulationCaptureList.as_view(), name="simulation-captures"),

    url(r'^simulations/(?P<name>[\w.@+-]+)/logs$', SimulationLogs.as_view(), name="simulation-messages"),

    url(r'^simulations/(?P<lab>[\w.@+-]+)/data/all$', SimulationAllLabData.as_view(), name="simulation-lab-data"),

    url(r'^simulations/(?P<lab>[\w.@+-]+)/data/(?P<user>[\w.@+-]+)$', SimulationUserLabData.as_view(), name="simulation-lab-data"),

    # url(r'^selfservice/validate$', SimulationCreateSelfServe.as_view(), name="virlfile-valdidate"),

    #cohort-list
url(r'^cohorts/$', CohortsListView.as_view(), name="cohort-list"),
]



