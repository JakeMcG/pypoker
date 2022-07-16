import json
import core.models as models
import itertools
import datetime, pytz
from core.interfaces import bcp
import os

HANDS_FOLDER = "tests/hands/"

def getHandJson(fileName):
    with open(HANDS_FOLDER + fileName + ".json") as f:
        data = json.load(f)
    return data

def getHandObject(fileName):
    return models.Hand.objects.annotated().get(site_key=getHandJson(fileName)["key"])

def testFileNames():
    for f in os.listdir(HANDS_FOLDER):
        if not os.path.isfile(HANDS_FOLDER + f): continue
        fp = f.split(".")
        if fp[1] != "json": continue
        yield fp[0]

def storeTestHandsToDb():
    models.Table.objects.all().delete()
    models.Hand.objects.all().delete()
    
    for f in testFileNames():
        data = getHandJson(f)
        t = models.Table.objects.create(name=data["name"])
        models.Hand.objects.create(
            site_key=data["key"],
            table=t,
            played_time=datetime.datetime.utcnow().replace(tzinfo=pytz.UTC) 
        )
        bcp.storeHand(data)

def populateCardDb():
    models.PlayingCard.objects.all().delete()

    suits = models.PlayingCard.Suit.values
    ranks = ["2", "3", "4", "5", "6", "7", "8", "9", "T", "J", "Q", "K", "A"]
    assert(len(ranks) == 13)

    d = dict()
    for (i,r) in enumerate(ranks):
        d[r] = i+1 # 2 ranks 1, A ranks 13

    for (s, r) in itertools.product(suits, ranks):
        models.PlayingCard.objects.create(suit=s, rank=r, rank_integer=d[r])
