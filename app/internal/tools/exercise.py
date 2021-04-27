import pylxd
from ..lxd.client import client
from ..lxd.command import exec_command_to_instance
from ..lxd.image import download_ubuntu_image
from ..lxd.tag import instance_tag
from ..general.async_wrap import async_wrap


command_dict = {
    "ssh_keygen": [
        "touch /root/.ssh/id_rsa",
        "touch /root/.ssh/id_rsa.pub",
        "rm /root/.ssh/id_rsa",
        "rm /root/.ssh/id_rsa.pub",
        ["ssh-keygen", "-t", "rsa", "-N", "", "-f", "/root/.ssh/id_rsa"]
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

async def get_teacher_student_instance():
    

async def send_student_list(instance, student_instances):
    s_name_list = []
    for s_instance in student_instances:
        s_name_list.append(str(s_instance.name).encode('utf-8'))
    s_name_list = sorted(s_name_list)
    await async_wrap(instance.files.put)("/root/student_hostname",
                                         b"\n".join(s_name_list) + b"\n")


async def setup_ssh(class_id):
    all_instances = await async_wrap(client.instances.all)()
    teacher_instances = []
    student_instances = []
    for instance in all_instances:
        tag = instance_tag(instance)

        if "class_id" in tag.tag and "role_id" in tag.tag:
            if tag.tag["class_id"] == class_id and tag.tag["role_id"] == "teacher":
                teacher_instances.append(instance)
            elif tag.tag["class_id"] == class_id and tag.tag["role_id"] == "student":
                student_instances.append(instance)
        else:
            pass

    pubs = []

    if len(teacher_instances) == 0 or len(student_instances) == 0:
        return False
    for instance in teacher_instances:
        pubs.append(await gen_ssh_key(instance))
        await send_student_list(instance, student_instances)
    for instance in student_instances:
        await send_ssh_pub(instance, b"".join(pubs))

    return True


async def setup_syslog(class_id):
    pass