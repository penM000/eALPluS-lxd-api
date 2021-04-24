"""

def read_file(file_path):
    with open(file_path) as f:
        l_strip = [s.strip() for s in f.readlines()]
        return l_strip
def make_csv(
        in_file_path,
        out_file_path,
        start_port=0,
        prefix="",
        suffix="",
        image_aliases="",
        image_fingerprint="",
        class_code="",
        ip_address=""):
    members = read_file(in_file_path)
    port_offset = 0
    file_meta = ["class_code,name,ip,port,image_aliases,image_fingerprint"]
    for i in range(len(members)):
        while True:
            port_candidate = start_port + i + port_offset
            if check_port_available(port_candidate):
                file_meta.append(
                    class_code + "," +
                    members[i] + "," +
                    ip_address + "," +
                    str(port_candidate) + "," +
                    image_aliases + "," +
                    image_fingerprint
                )
                break
            else:
                port_offset += 1
    with open(out_file_path, mode='w') as f:
        f.write('\n'.join(file_meta))

def make_csv_from_str(
        in_file_str="",
        start_port=0,
        prefix="",
        suffix="",
        image_aliases="",
        image_fingerprint="",
        class_code="",
        ip_address=""):
    members = in_file_str.splitlines()
    port_offset = 0
    file_meta = ["class_code,name,ip,port,image_aliases,image_fingerprint"]
    for i in range(len(members)):
        while True:
            port_candidate = start_port + i + port_offset
            if check_port_available(port_candidate):
                file_meta.append(
                    class_code + "," +
                    members[i] + "," +
                    ip_address + "," +
                    str(port_candidate) + "," +
                    image_aliases + "," +
                    image_fingerprint
                )
                break
            else:
                port_offset += 1
    return '\n'.join(file_meta)


async def test():
    hoge = await wait_get_html("https://yukkuriikouze.com", 200, 5)
    print(hoge)


async def test():
    await asyncio.gather(exec_command_to_machine("funo", "sleep 10"), exec_command_to_machine("funo", "sleep 10"), exec_command_to_machine("funo", "sleep 10"))

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(test())



make_csv(
        'member.txt',
        'member.csv',
        start_port=10000,
        ip_address="160.252.131.148",
        class_code="PIT0014",
        image_aliases="PIT0014-v1")
    for line in read_file('member.csv')[1:]:
        class_code, name, ip, port, aliases, fingerprint = line.split(",")
        #print(class_code+"-"+name, port, aliases, fingerprint)
        print("launch"+class_code+"-"+name)
        #launch_container_machine(class_code+"-"+name, port)
    # launch_container_machine("my-test2","5659")
    # delete_machine("my-vmapitest")
"""
