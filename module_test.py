from app.internal.lxd.cluster import check_cluster

if __name__ == "__main__":
    import asyncio
    loop = asyncio.get_event_loop()
    hoge = loop.run_until_complete(check_cluster())
    print(hoge)
