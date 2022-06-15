from getpass import getpass
from core.interfaces import network 
import json

# utility script to pull an arbitrary hand from blockchain.poker to a json file
# usage: util.py hand KEY
def handToJsonFile(handKey):

    u = input("Username: ")
    p = getpass()

    try:
        socket = network.BcpSocketInterface()
        if socket.authenticate(u, p):
            hand = socket.getHand(handKey)

            with open(handKey + '.json', 'w') as file:
                file.write(json.dumps(hand))
        else:
            print("Authentication failed.")
    except:
        print("Something went wrong.")
        