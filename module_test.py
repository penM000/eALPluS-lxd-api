from app.internal.lxd.cluster import check_cluster, get_cluster_status

if __name__ == "__main__":
    import asyncio
    loop = asyncio.get_event_loop()
    hoge = loop.run_until_complete(check_cluster())
    print(hoge)
    hoge = loop.run_until_complete(get_cluster_status())
    print(hoge)
