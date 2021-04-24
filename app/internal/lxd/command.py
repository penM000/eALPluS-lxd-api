import shlex
from typing import Union

import pylxd

from ..general.async_wrap import async_wrap

# マシンコマンド実行


async def exec_command_to_machine(machine: Union[pylxd.models.VirtualMachine,
                                                 pylxd.models.Container], cmd):
    async_machine_execute = async_wrap(machine.execute)
    result = await async_machine_execute(shlex.split(cmd))
    return result
