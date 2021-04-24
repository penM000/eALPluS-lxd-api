from .client import client
from ..general.async_wrap import async_wrap


async def launch_container_machine(
        hostname: str = "",
        cpu: int = 2,
        memory: str = "4GB",
        disk_size: str = "32GB",
        fingerprint: str = "",
        aliases: str = "",
        network: str = "lxdbr0",
        role_id: str = "",
        class_id: str = ""):
    image = {}
    if fingerprint != "":
        image = {"type": "image", "fingerprint": str(fingerprint)}
    elif aliases != "":
        image = {"type": "image", "alias": str(aliases)}
    config = {
        "name": str(hostname),
        "source": image,
        "config": {
            "limits.cpu": str(cpu),
            "limits.memory": str(memory),
            "security.nesting": "1",
            "user.role": str(role_id),
            "user.class": str(class_id)},
        "devices": {
            "eth0": {
                "name": "eth0",
                "network": str(network),
                "type": "nic"
            },
            "root": {
                "path": "/",
                "pool": "default",
                "size": str(disk_size),
                "type": "disk",
            }
        }
    }
    async_execute = async_wrap(client.containers.create)
    container = await async_execute(config, wait=True)
    async_execute = async_wrap(container.start)
    await async_execute(wait=True)


def launch_virtual_machine():
    config = {
        "name": "my-vmapitest",
        "source": {
            "type": "image",
            "fingerprint": "fbca989572df"},
        "config": {
            "limits.cpu": "2",
            "limits.memory": "3GB"},
        "devices": {
            "root": {
                "path": "/",
                "pool": "default",
                "type": "disk",
                "size": "20GB"}}}
    virtual_machines = client.virtual_machines.create(config, wait=True)
    virtual_machines.start(wait=True)
