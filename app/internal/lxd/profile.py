from .client import client


def get_default_profile():
    profile = client.profiles.get("default")

    print(profile.config)



