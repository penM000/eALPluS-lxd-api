from .client import client
from .storage import get_all_storage_pool
from .tag import instance_tag
from ..general.async_wrap import async_wrap


async def launch_container_instance(
        hostname: str = "",
        cpu: int = 2,
        memory: str = "4GB",
        disk_size: str = "32GB",
        fingerprint: str = "",
        aliases: str = "",
        network: str = "lxdbr0",
        instance_type: str = "container",
        role_id: str = "",
        class_id: str = "",
        autostart:str = "0"):
    """
    container
    virtual-machine
    """
    image = {}
    if fingerprint != "":
        image = {"type": "image", "fingerprint": str(fingerprint)}
    elif aliases != "":
        image = {"type": "image", "alias": str(aliases)}
    config = {
        "name": str(hostname),
        "source": image,
        "type": str(instance_type),
        "config": {
            "limits.cpu": str(cpu),
            "limits.memory": str(memory),
            "security.nesting": "1",
            "boot.autostart": str(autostart)
        },
        "devices": {
            "eth0": {
                "name": "eth0",
                "network": str(network),
                "type": "nic"
            },
            "root": {
                "path": "/",
                "pool": str(get_all_storage_pool()[0]),
                "size": str(disk_size),
                "type": "disk",
            }
        }
    }
    try:
        # インスタンスの作成
        instance = await async_wrap(client.containers.create)(config, wait=True)
        # インスタンス情報の付与
        tag = instance_tag(instance)
        tag.tag["creating"] = "1"
        tag.tag["role_id"] = role_id
        tag.tag["class_id"] = class_id
        await async_wrap(tag.save)()
        # インスタンスの起動
        await async_wrap(instance.start)(wait=True)
        # 初回起動の終了記録
        tag.tag["creating"] = "0"
        await async_wrap(tag.save)()

        print(f"create new instance:{hostname}")
        return instance
    except BaseException:
        return None


def launch_virtual_instance():
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
    virtual_instances = client.virtual_instances.create(config, wait=True)
    virtual_instances.start(wait=True)
