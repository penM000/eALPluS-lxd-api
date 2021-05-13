from typing import List
from fastapi import APIRouter, Request
from ...internal.lxd.network import get_ip_address
from ...internal.lxd.port import get_listen_status
from ...internal.lxd.cluster import get_all_node_used_port

router = APIRouter(
    prefix="/node",
    responses={404: {"description": "Not found"}},
    tags=["node"],
)


@router.get("/ip")
async def get_ip(request: Request):
    """
    ipアドレスの値を取得
    """
    return get_ip_address(request.client.host)[0]


@router.get("/used_port")
async def used_port() -> List[int]:
    """
    ipアドレスの値を取得
    """
    return await get_listen_status()


@router.get("/all_node_used_port")
async def used_port() -> List[int]:
    """
    ipアドレスの値を取得
    """
    return await get_all_node_used_port()
