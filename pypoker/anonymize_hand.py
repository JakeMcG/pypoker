import sys
import json
import random
import string

NAMES = ["Phil H",
        "Daniel N",
        "Tony G",
        "Erik S",
        "Doyle B",
        "Phil I",
        "Mike M",
        "Tom D",
        "Phil L"]

def anonymizeHand(fileName):
    with open(fileName, 'r') as fi:
        data = json.load(fi)
        # overwrite table name
        data["name"] = "Table Name"
        # overwrite key
        key = "".join(random.choices(string.ascii_lowercase + string.digits, k=10))
        data["key"] = key
        # anonymize player names
        for (i,s) in enumerate(data["seats"]):
            s["name"] = NAMES[i]
        with open(key + ".json", "w+") as fo:
            json.dump(data, fo, indent=4)    

if __name__ == "__main__":
    anonymizeHand(sys.argv[1])