import requests
import json
from pprint import pprint


def getMcServerInfo(adress):
    req = requests.get(f"https://api.mcsrvstat.us/3/{adress}")

    data = json.loads(req.text)
    out = {}
    out["motd"] = data["motd"]["clean"]
    out["version"] = data["version"]
    out["players"] = data["players"]["online"]
    try:
        out["players list"] = data["players"]["list"]
    except KeyError:
        out["players list"] = []
    out["max players"] = data["players"]["max"]
    out["is online"] = data["online"]
    out["adress"] = data["ip"] + ":" + str(data["port"])
    return out


if __name__ == "__main__":
    adress = "185.9.145.219:25809"
    data = getMcServerInfo(adress)
    pprint(data)