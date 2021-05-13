from ..general.async_wrap import async_wrap
from .client import client


async def check_cluster():
    cluster = await async_wrap(client.cluster.get)()
    return cluster.enabled


async def get_cluster_status():
    cluster = await async_wrap(client.cluster.get)()
    members = await async_wrap(cluster.members.all)()
    for node in members:
        print(f"name={node.server_name}  url={node.url}  ")
