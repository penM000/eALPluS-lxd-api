
from fastapi import APIRouter, Request
from starlette.responses import RedirectResponse


from ...internal.lxd.instance import (launch_instance,
                                      get_instance,
                                      stop_instance)
from ...internal.lxd.network import get_ip_address


from ...internal.general.response import make_response_dict
from ...internal.general.exercise import setup_ssh


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


@router.get("/container/url/{course_id}/{student_id}")
async def get_container_url(course_id: str,
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
    course_id = 授業コード(イメージ名)\n
    student_id = 学籍番号(授業コード内で一意に定まるもの)
    """

    if image == "":
        imagealias = course_id
    else:
        imagealias = image
    result = await launch_instance(hostname=f"{course_id}-{student_id}",
                                   imagealias=imagealias,
                                   network=course_id,
                                   src_port=src_port,
                                   port_name=port_name,
                                   class_id=course_id,
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


@router.get("/container/ip_port/{course_id}/{student_id}")
async def get_container_ip_port(course_id: str,
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
    course_id = 授業コード(イメージ名)\n
    student_id = 学籍番号(授業コード内で一意に定まるもの)
    """

    if image == "":
        imagealias = course_id
    else:
        imagealias = image
    result = await launch_instance(hostname=f"{course_id}-{student_id}",
                                   imagealias=imagealias,
                                   network=course_id,
                                   src_port=src_port,
                                   port_name=port_name,
                                   class_id=course_id,
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


@router.get("/container/stop/{course_id}/{student_id}")
async def stop_container_by_course_id_student_id(course_id: str,
                                                 student_id: str,
                                                 ):
    """
    インスタンスを停止します。\n
    course_id = 授業コード(イメージ名)\n
    student_id = 学籍番号(授業コード内で一意に定まるもの)
    """
    instance = await get_instance(f"{course_id}-{student_id}")
    if instance is None:
        return make_response_dict(False, "インスタンスが見つかりません")
    if instance.status == "Running":
        await stop_instance(instance)
        return make_response_dict(True, "インスタンスを停止しました")
    else:
        return make_response_dict(False, "インスタンスは既に停止しています")


@router.get("/container/ssh_setup/{course_id}")
async def setup_ssh_by_course_id(course_id):
    return await setup_ssh(course_id)
