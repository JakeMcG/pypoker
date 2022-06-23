import json
import core.models as models
import itertools
import datetime
from core.interfaces import bcp

TEST_FILES = {
    "baseline": "hand_baseline.json",
    "big_blind_steal": "hand_bb_steal.json"
}

def getHandJson(key):
    with open("tests/" + TEST_FILES[key]) as f:
        data = json.load(f)
    return data

def storeTestHandsToDb():
    models.Table.objects.all().delete()
    models.Hand.objects.all().delete()

    for k in TEST_FILES.keys():
        data = getHandJson(k)
        t = models.Table.objects.create(name=data["name"])
        models.Hand.objects.create(
            site_key=data["key"],
            table=t,
            time_stamp=datetime.datetime.now()
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
