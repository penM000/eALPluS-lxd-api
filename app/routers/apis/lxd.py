import time
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from starlette.responses import RedirectResponse
from typing import List


from ...internal.lxd_machine import launch_machine, get_port
from ...internal.lxd_network import create_network, \
    scan_available_port, \
    get_ip_address
from ...internal.lxd_client import client


router = APIRouter(
    prefix="/lxd",
    responses={404: {"description": "Not found"}},
)


@router.get("/ip")
async def get_ip(request: Request):
    """
    ipアドレスの値を取得
    """
    return get_ip_address(request.client.host)[0]


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


@router.get("/container/device/{name}")
async def get_network(name: str):
    used_ports = {}
    machine = client.containers.get(name)
    for key in machine.devices:
        if "type" in machine.devices[key]:
            if machine.devices[key]["type"] == "proxy":
                dst_port = int(machine.devices[key]["listen"].split(":")[-1])
                src_port = int(machine.devices[key]["connect"].split(":")[-1])
                used_ports[key] = {"src_port": src_port, "dst_port": dst_port}
    print("hoge", used_ports)
    return


@router.get("/container/url/{course_id}/{student_id}")
async def get_container_url(course_id: str,
                            student_id: str,
                            request: Request,
                            src_port: int = 8080,
                            port_name: str = "vscode-port",
                            image: str = ""
                            ):
    """
    course_id = 授業コード(イメージ名)\n
    student_id = 学籍番号(授業コード内で一意に定まるもの)
    """
    now = time.time()
    if image == "":
        imagealias = course_id
    else:
        imagealias = image
    result = await launch_machine(hostname=f"{course_id}-{student_id}",
                                  imagealias=imagealias,
                                  network=course_id,
                                  src_port=src_port,
                                  port_name=port_name)
    print(time.time() - now)
    if result["status"]:
        #ipaddr = "192.168.1.80"
        ipaddr = get_ip_address(request.client.host)[0]
        port = result["assign_port"]
        # print(f"http://{ipaddr}:{port}")
        response = RedirectResponse(url=f"http://{ipaddr}:{port}")

        return response
    else:
        return result
