from typing import Dict
import pylxd


class instance_tag():
    def __init__(self, instance):
        self.instance: pylxd.models.instance.Instance = instance
        self.usertag = dict()
        self.limits = dict()
        self.get()

    def get(self) -> Dict[str, str]:
        for key in self.instance.config.keys():
            if key.startswith("user."):
                self.usertag[key[5:]] = self.instance.config[key]

            if key.startswith("limits."):
                self.limits[key[5:]] = self.instance.config[key]
        return self.usertag, self.limits

    def save(self):
        config = dict()
        for key in self.usertag.keys():
            config[f"user.{key}"] = str(self.usertag[key])

        for key in self.limits.keys():
            config[f"limits.{key}"] = str(self.limits[key])

        self.instance.config.update(config)
        try:
            self.instance.save(wait=True)
            return True
        except Exception:
            return False
