from fastapi import APIRouter, Depends, HTTPException,Query
from starlette.responses import RedirectResponse
from typing import List
from pylxd import Client

"""
client = Client(
    endpoint='http://10.0.0.1:8443',
    cert=('lxd.crt', 'lxd.key'))
"""
Client()
client = Client(endpoint="https://192.168.1.80:8443",verify=False)
client.authenticate("password")
print(client.trusted)


router = APIRouter(
    prefix="/lxd",
    tags=["lxd"],
    responses={404: {"description": "Not found"}},
)
@router.get("/")
async def get_cluster():
    return "ok"