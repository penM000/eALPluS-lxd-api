from typing import Union
import pylxd
from ..general.async_wrap import async_wrap
# ファイル送信


async def send_file_to_instance(instance: Union[pylxd.models.VirtualMachine,
                                                pylxd.models.Container],
                                filename: str,
                                filemetadata: str):
    if filename[0] != "/":
        filename = "/" + filename
    async_instance_file_put = async_wrap(instance.files.put)
    try:
        await async_instance_file_put(filename, filemetadata)
        return True
    except BaseException:
        return False


def get_instance_file(instance, file_path, local_path):
    file_meta = instance.files.recursive_get(file_path, local_path)

    return file_meta
