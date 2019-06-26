import  os
from django.dispatch import receiver
# from constance import config
# from constance.signals import config_updated



#VIRAL Credentials
VIRL_USERNAME = "guest"
# VIRL_PASSWORD = "Meilab123"
VIRL_PASSWORD = "gCableNetw0rk5"


#MEDIA FOLDER LOCATION (WHERE TOPOLOGY IS SAVED)


MEDIA_PATH = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))

# LAB_PER_VIRL = config.SIMULATION_PER_SERVER
LAB_PER_VIRL = 2
MAX_BAD_FLAG = 3



# @receiver(config_updated)
# def constance_updated(sender, key, old_value, new_value, **kwargs):
#     if old_value != new_value:
#         LAB_PER_VIRL = new_value
#
