import shlex
from typing import Union

import pylxd

from ..general.async_wrap import async_wrap

# マシンコマンド実行


async def exec_command_to_instance(instance: pylxd.models.instance.Instance,
                                   cmd: Union[str, list]):
    if isinstance(cmd, list):
        for i in cmd:
            if isinstance(i, str):
                temp = shlex.split(i)
            elif isinstance(i, list):
                temp = i
            result = await async_wrap(instance.execute)(temp)
    else:
        cmd = shlex.split(cmd)
        result = await async_wrap(instance.execute)(cmd)
        return result
