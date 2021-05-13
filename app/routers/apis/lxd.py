
from fastapi import APIRouter, Request

from starlette.responses import RedirectResponse


from ...internal.lxd.instance import (launch_instance,
                                      get_instance,
                                      stop_instance,
                                      operation_of_class_instances)


from ...internal.general.response import make_response_dict
from ...internal.tools.exercise import setup_ssh, setup_syslog


router = APIRouter(
    prefix="/lxd/container/",
    responses={404: {"description": "Not found"}},
)


@router.get("url/{class_id}/{student_id}")
async def get_container_url(class_id: str,
                            student_id: str,
                            request: Request,
                            src_port: int = 8080,
                            port_name: str = "vscode-port",
                            image: str = "",
                            ealps_role: str = "",
                            cpu: int = 2,
                            memory: str = "2GB",
                            storage: str = "32GB"
                            ):
    """
    class_id = 授業コード(イメージ名)\n
    student_id = 学籍番号(授業コード内で一意に定まるもの)
    """

    if image == "":
        imagealias = class_id
    else:
        imagealias = image
    result = await launch_instance(hostname=f"{class_id}-{student_id}",
                                   imagealias=imagealias,
                                   network=class_id,
                                   src_port=src_port,
                                   port_name=port_name,
                                   class_id=class_id,
                                   role_id=ealps_role,
                                   cpu=cpu,
                                   memory=memory,
                                   storage=storage)

    if result["status"]:
        # ipaddr = "192.168.1.80"
        ipaddr = get_ip_address(request.client.host)[0]
        port = result["assign_port"]
        # print(f"http://{ipaddr}:{port}")
        response = RedirectResponse(url=f"http://{ipaddr}:{port}")

        return response
    else:
        return result


@router.get("ip_port/{class_id}/{student_id}")
async def get_container_ip_port(class_id: str,
                                student_id: str,
                                request: Request,
                                src_port: int = 8080,
                                port_name: str = "vscode-port",
                                image: str = "",
                                ealps_role: str = "",
                                cpu: int = 2,
                                memory: str = "2GB",
                                storage: str = "32GB"
                                ):
    """
    class_id = 授業コード(イメージ名)\n
    student_id = 学籍番号(授業コード内で一意に定まるもの)
    """

    if image == "":
        imagealias = class_id
    else:
        imagealias = image
    result = await launch_instance(hostname=f"{class_id}-{student_id}",
                                   imagealias=imagealias,
                                   network=class_id,
                                   src_port=src_port,
                                   port_name=port_name,
                                   class_id=class_id,
                                   role_id=ealps_role,
                                   cpu=cpu,
                                   memory=memory,
                                   storage=storage)
    # print(time.time() - now)
    if result["status"]:
        # ipaddr = "192.168.1.80"
        ipaddr = get_ip_address(request.client.host)
        port = result["assign_port"]
        # print(f"http://{ipaddr}:{port}")
        return {"ip": ipaddr[0], "port": port}
    else:
        return result


@router.get("stop/{class_id}/{student_id}")
async def stop_container_by_class_id_student_id(class_id: str,
                                                student_id: str,
                                                ):
    """
    インスタンスを停止します。\n
    class_id = 授業コード(イメージ名)\n
    student_id = 学籍番号(授業コード内で一意に定まるもの)
    """
    instance = await get_instance(f"{class_id}-{student_id}")
    if instance is None:
        return make_response_dict(False, "インスタンスが見つかりません")
    if instance.status == "Running":
        await stop_instance(instance)
        return make_response_dict(True, "インスタンスを停止しました")
    else:
        return make_response_dict(False, "インスタンスは既に停止しています")


@router.get("ssh_setup/{class_id}")
async def setup_ssh_by_class_id(class_id):
    return await setup_ssh(class_id)


@router.get("syslog_setup/{class_id}")
async def setup_syslog_by_class_id(class_id):
    return await setup_syslog(class_id)


@router.get("start/{class_id}")
async def start_container_by_class_id(class_id: str):
    return await operation_of_class_instances(class_id, "start")


@router.get("stop/{class_id}")
async def stop_container_by_class_id(class_id: str):
    return await operation_of_class_instances(class_id, "stop")


@router.get("delete/{class_id}")
async def delete_container_by_class_id(class_id: str):
    return await operation_of_class_instances(class_id, "delete")
