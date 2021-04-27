import os
import pylxd
from ..lxd.client import client
from ..lxd.command import exec_command_to_instance
from ..lxd.image import download_ubuntu_image
from ..lxd.launch import launch_container_instance
from ..lxd.tag import instance_tag
from ..lxd.instance import get_instance
from ..lxd.network import create_network
from ..general.async_wrap import async_wrap


command_dict = {
    "ssh_keygen": [
        "touch /root/.ssh/id_rsa",
        "touch /root/.ssh/id_rsa.pub",
        "rm /root/.ssh/id_rsa",
        "rm /root/.ssh/id_rsa.pub",
        ["ssh-keygen", "-t", "rsa", "-N", "", "-f", "/root/.ssh/id_rsa"]
    ],
    "receive_syslog": [
        "chmod +x /receive_syslog_setting.sh",
        "/receive_syslog_setting.sh",
    ],
    "send_syslog": [
        "chmod +x /send_syslog_setting.sh",
        "/send_syslog_setting.sh",
    ]
}


async def gen_ssh_key(instance: pylxd.models.instance.Instance):
    if instance.status != "Running":
        await async_wrap(instance.start)(wait=True)
    await exec_command_to_instance(instance, command_dict["ssh_keygen"])
    return await async_wrap(instance.files.get)("/root/.ssh/id_rsa.pub")


async def send_ssh_pub(instance, pub):
    await async_wrap(instance.files.put)("/home/ubuntu/.ssh/authorized_keys",
                                         pub)


async def get_teacher_and_student_instances(class_id):
    all_instances = await async_wrap(client.instances.all)()
    teacher_instances = []
    student_instances = []
    syslog_instances = []
    for instance in all_instances:
        tag = instance_tag(instance)
        # インスタンスに識別がある場合
        if "class_id" in tag.tag and "role_id" in tag.tag:
            if tag.tag["class_id"] == class_id:
                if tag.tag["role_id"] == "teacher":
                    teacher_instances.append(instance)
                elif tag.tag["role_id"] == "student":
                    student_instances.append(instance)
                elif tag.tag["role_id"] == "syslog":
                    syslog_instances.append(instance)
        else:
            pass
    result = {
        "teacher": teacher_instances,
        "student": student_instances,
        "syslog": syslog_instances
    }
    return result


async def send_student_list(instance, student_instances):
    s_name_list = []
    for s_instance in student_instances:
        s_name_list.append(str(s_instance.name).encode('utf-8'))
    s_name_list = sorted(s_name_list)
    await async_wrap(instance.files.put)("/root/student_hostname",
                                         b"\n".join(s_name_list) + b"\n")


async def setup_ssh(class_id):
    instances = await get_teacher_and_student_instances(class_id)

    if len(instances["teacher"]) == 0 or len(instances["student"]) == 0:
        return False

    pubs = []
    for instance in instances["teacher"]:
        pubs.append(await gen_ssh_key(instance))
        await send_student_list(instance, instances["student"])

    for instance in instances["student"]:
        await send_ssh_pub(instance, b"".join(pubs))

    for instance in instances["syslog"]:
        await send_ssh_pub(instance, b"".join(pubs))

    return True


async def setup_receive_syslog(class_id):
    hostname = f"{class_id}-syslog-server"
    network = class_id
    instance = await get_instance(hostname)
    # マシンが無ければ新規作成
    if None is instance:
        # ネットワーク作成
        await create_network(network)
        image = await download_ubuntu_image()
        instance = await launch_container_instance(
            hostname=hostname,
            fingerprint=image.fingerprint,
            network=network,
            role_id="syslog",
            class_id=class_id
        )
    if instance.status != "Running":
        await async_wrap(instance.start)(wait=True)
    filedata = open(
        "./app/internal/tools/script/receive_syslog_setting.sh").read()
    await async_wrap(instance.files.put)("/receive_syslog_setting.sh", filedata)
    await exec_command_to_instance(instance, command_dict["receive_syslog"])


async def setup_send_syslog(instances, class_id):
    hostname = f"{class_id}-syslog-server"
    filedata = open(
        "./app/internal/tools/script/send_syslog_setting.sh").read()
    filedata = filedata.replace("syslog-server", hostname).encode()
    for instance in instances:
        if instance.status != "Running":
            await async_wrap(instance.start)(wait=True)
        print(instance.name)
        await async_wrap(instance.files.put)("/send_syslog_setting.sh", filedata)
        await exec_command_to_instance(instance, command_dict["send_syslog"])


async def setup_syslog(class_id):
    result = await get_teacher_and_student_instances(class_id)
    teacher_instances = result["teacher"]
    student_instances = result["student"]
    if len(teacher_instances) == 0 or len(student_instances) == 0:
        # return False
        pass

    await setup_receive_syslog(class_id)
    await setup_send_syslog(teacher_instances, class_id)
    await setup_send_syslog(student_instances, class_id)
    return True
