from typing import List, Union
from .lxd_client import client


def get_all_image():
    aliases = []
    fingerprint = []
    for image in client.images.all():
        if len(image.aliases) != 0:
            for i in image.aliases:
                if "name" in i:
                    aliases.append(i["name"])
        fingerprint.append(image.fingerprint)
    return aliases, fingerprint


def check_existence_of_image(
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
