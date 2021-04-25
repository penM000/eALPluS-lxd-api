import os
from pylxd import Client


"""
client = Client(
    endpoint='http://10.0.0.1:8443',
    cert=('lxd.crt', 'lxd.key'))
"""

"""
client = Client(endpoint="https://192.168.1.80:8443", verify=False)
client.authenticate("password")

"""
os.environ["PYLXD_WARNINGS"] = "none"
client = Client()
