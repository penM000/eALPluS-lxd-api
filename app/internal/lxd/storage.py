from .client import client


def get_all_storage_pool():
    temp = []
    hoge = client.storage_pools.all()
    for i in hoge:
        temp.append(i.name)

    return temp
