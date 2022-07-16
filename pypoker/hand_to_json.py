import sys
from getpass import getpass
from core.interfaces import network 
import json

# utility script to pull an arbitrary hand from blockchain.poker to a json file
# usage: util.py hand KEY
def handToJsonFile(handKey):
    print(handKey)
    u = input("Username: ")
    p = getpass()

    with network.BcpSocketInterface() as socket:
        if socket.authenticate(u, p):
            hand = socket.getHand(handKey)

            with open(handKey + '.json', 'w') as file:
                file.write(json.dumps(hand))
        else:
            print("Authentication failed.")

if __name__ == "__main__":
    handToJsonFile(sys.argv[1])