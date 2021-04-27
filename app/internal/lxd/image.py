import time
from typing import List, Union
from functools import lru_cache

import pylxd

from .client import client
from ..general.async_wrap import async_wrap

cache_timer = 0


def get_all_image():
    global cache_timer
    if time.time() - cache_timer > 10:
        cache_get_all_image.cache_clear()
        cache_timer = time.time()
    return cache_get_all_image()


@lru_cache(maxsize=10)
def cache_get_all_image():
    aliases = []
    fingerprint = []
    for image in client.images.all():
        if len(image.aliases) != 0:
            for i in image.aliases:
                if "name" in i:
                    aliases.append(i["name"])
        fingerprint.append(image.fingerprint)
    return aliases, fingerprint


async def check_existence_of_image(
        alias: str = "", finger: str = "") -> List[Union[bool, str]]:
    aliases, fingerprint = get_all_image()
    if (alias == "") and (finger == ""):
        return [False, "イメージが指定されていません"]

    elif alias != "" and \
            len([s for s in aliases if alias == s]) == 0:
        return [False, f"指定された「{alias}」イメージエイリアスが見つかりません"]

    elif finger != "" and \
            len([s for s in fingerprint if s.startswith(finger)]) == 0:
        return [False, f"指定された「{finger}」イメージフィンガープリントが見つかりません"]
    return [True, None]


async def download_ubuntu_image() -> pylxd.models.image.Image:
    image = await async_wrap(client.images.create_from_simplestreams)(
        server="https://cloud-images.ubuntu.com/releases",
        alias="ubuntu",
        auto_update=True)
    return image
