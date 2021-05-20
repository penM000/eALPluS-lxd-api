from typing import Dict
import pylxd


class instance_tag():
    def __init__(self, instance):
        self.instance: pylxd.models.instance.Instance = instance
        self.tag = dict()
        self.tag = self.get()

    def get(self) -> Dict[str, str]:
        for key in self.instance.config.keys():
            if key.startswith("user."):
                self.tag[key[5:]] = self.instance.config[key]
        return self.tag

    def save(self):
        tag = dict()
        for key in self.tag.keys():
            tag[f"user.{key}"] = str(self.tag[key])
        self.instance.config.update(tag)
        try:
            self.instance.save(wait=True)
            return True
        except Exception:
            return False
