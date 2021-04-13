from fastapi import APIRouter, Depends, HTTPException, Query
from starlette.responses import RedirectResponse
from typing import List


from ...internal.lxd_machine import launch_machine, get_port
from ...internal.lxd_network import create_network, get_ip
from ...internal.lxd_client import client


router = APIRouter(
    prefix="/lxd",
    tags=["lxd"],
    responses={404: {"description": "Not found"}},
)


@router.get("/ip")
async def get_cluster():
    return get_ip()


@router.get("/image")
async def get_cluster():
    for i in client.images.all():
        print(i.aliases)
    return


@router.get("/cluster")
async def get_cluster():
    cluster = client.cluster.get()
    members = cluster.members.all()
    return members


@router.get("/container")
async def get_container():
    names = list()
    for i in client.containers.all():
        names.append(i.name)
    return names


@router.get("/container/{prefix}")
async def get_container_prefix(prefix: str):
    names = list()
    for i in client.containers.all():
        if str(i.name).startswith(prefix):
            names.append(i.name)
    return names


@router.get("/container/delete/{name}")
async def get_container_prefix(name: str):
    if client.containers.exists(name):
        client.containers.get(name).stop(wait=True)
        client.containers.get(name).delete(wait=True)
        return True
    return False


@router.get("/container/delete/prefix/{prefix}")
async def get_container_prefix(prefix: str):
    containers = list()
    for i in client.containers.all():
        if str(i.name).startswith(prefix):
            containers.append(i)
    for container in containers:
        container.stop(wait=True)
        container.delete(wait=True)


@router.get("/network")
async def get_network():
    for i in client.networks.all():
        print(i.name)
    return


@router.get("/network/{name}")
async def get_network(name: str):
    return client.networks.get(name)


@router.get("/network/create/{name}")
async def get_network(name: str):
    await create_network(name)
    return client.networks.get(name)


@router.get("/container/url/{course_id}/{student_id}")
async def get_container_url(course_id: str,
                            student_id: str,
                            src_port: int = 8080,
                            port_name: str = "vscode-port"):
    """
    course_id = 授業コード(イメージ名)\n
    student_id = 学籍番号(授業コード内で一意に定まるもの)
    """
    result = await launch_machine(hostname=f"{course_id}-{student_id}",
                                  imagealias=course_id,
                                  network=course_id,
                                  src_port=src_port,
                                  port_name=port_name)
    if result["status"]:
        ipaddr = "192.168.1.80"
        port = result["assign_port"]
        print(f"http://{ipaddr}:{port}")
        response = RedirectResponse(url=f"http://{ipaddr}:{port}")

        return  # response
    else:
        return result
