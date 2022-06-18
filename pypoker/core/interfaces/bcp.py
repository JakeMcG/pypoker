import core.models as models
import datetime
from . import network

FORCE_CREATE = False

def loadRecentHandsToDb(username, password):
    result = {
        "error": False,
        "errorText": "",
        "newHands": 0,
        "earliestHandTime": "", # call lastest/earliest to avoid confusion, since later hands loaded first
        "latestHandTime": ""} # result of import to feed to front-end
    
    socket = network.BcpSocketInterface()
    
    try:
        (authSuccess, authResponse) = socket.authenticate(username, password)
        if authSuccess:
            storeHero(authResponse)

            handHistory = socket.getHandHistory()
            for hh in handHistory:
                # hand history is reverse chronological
                # so once we find one that exists, the loop can break
                t = models.Table.objects.get_or_create(
                    name=hh["tableName"])

                h = models.Hand.objects.get_or_create(site_key=hh["key"],
                    table=t[0],
                    time_stamp=convertBcpTime(hh["timestamp"]))

                if h[1] or FORCE_CREATE:
                    # this means a new hand has been created               
                    hand = socket.getHand(hh["key"])
                    # if there's a problem, hand's json contains an "error" field
                    if "error" in hand:
                        continue
                    storeHand(hand)
                    result["newHands"] += 1
                    if result["newHands"] == 1:
                        result["latestHandTime"] = hh["timestamp"]
                    result["earliestHandTime"] = hh["timestamp"]
                else:
                    break # an existing hand has been found, assume all earlier hands also exist
        else:
            result["error"] = True
            result["errorText"] = "Authentication failed."
                            
    except Exception as e:
        print(e)
        socket.tearDown()
        result["error"] = True
        result["errorText"] = str(e)
        return result

    socket.tearDown()
    return result

def storeHero(authResponse: dict):
    p = models.Player.objects.get_or_create(
        account_number=authResponse["account"]["id"],
        user_name=authResponse["account"]["name"])
    p[0].is_hero = True
    p[0].save()

def storeHand(hand: dict):  
    # hand object already exists from caller, update with additional info  
    h = models.Hand.objects.get(site_key=hand["key"])
    h.big_blind = hand["blinds"]["big"]
    h.save()

    # store hand-specific info
    for r in hand["rounds"]:
        cards = r["community"]
        if r["round"] == "FLOP":
            for c in cards:
                h.flop_cards.add(cardModelFromJson(c))
        elif r["round"] == "TURN":
            h.turn_card = cardModelFromJson(cards[0])
        elif r["round"] == "RIVER":
            h.river_card = cardModelFromJson(cards[0])
    h.save()

    # store seat specific info
    for seat in hand["seats"]:
        p = models.Player.objects.get_or_create(
            user_name=seat["name"],
            account_number=seat["account"])
        s = models.Seat.objects.create(
            player=p[0],
            hand=h,
            is_winner=seat["placing"]==1,
            is_big_blind=seat["isBigBlind"],
            is_small_blind=seat["isSmallBlind"],
            starting_stack=getStartingStack(seat),
            winnings=seat["winnings"]
        )
        # Note: seat["stack"] is at END of hand
        for c in getHoleCards(seat):
            # if no hole cards revealed, this loop won't run
            s.hole_cards.add(c)
            s.hole_cards_shown = True
        s.save()

    # store actions
    actions = getActionsByRound(hand["seats"], hand["rounds"])
    # list of dicts, augmented version of bcp actions
    for (n,a) in enumerate(actions):
        models.Action.objects.create(
            seat=models.Seat.objects.get(
                hand=h,
                player__user_name=a["player"]),
            type=a["type"],
            amount=a["amount"],
            round=a["round"],
            number=n+1)  

    # store player positions
    for (player,pos) in getPlayerPositions(actions).items():
        models.Seat.objects.filter(
            hand=h,
            player__user_name=player).update(
            position=pos)

# stack in BCP response appears to be after pot contributions but before winnings
def getStartingStack(seat):
    return sum([a["amount"] for a in seat["actions"] if a["amount"] is not None], seat["stack"])

def convertBcpTime(timeStr):
    return datetime.datetime.strptime(
        timeStr,
        "%Y-%m-%dT%H:%M:%S.%fZ"
    )    

def getPlayerPositions(actions):
    # returns dict: player: position
    # to get player positions: iterate over actions pre-flop actions sorted by time
    # UTG is defined as position 1, so blinds shall not precede other pre-flop betting
    # big-blind is forcibly appended to list of actions, so it's not missed if every player folds to the BB
    # (in this case, BB wins without an action, other than their POST_BLIND)
    preflop = list(filter(lambda a: a["round"] == "PREFLOP" and a["type"] != "POST_BLIND", actions))
    blinds = list(filter(lambda a: a["type"] == "POST_BLIND", actions))
    bigBlind = max(blinds, key=lambda a: a["amount"])
    preflop.append(bigBlind)

    out = {}
    for (p,a) in enumerate(preflop):
        if a["player"] in out:
            # already seen player, therefore second action
            break     
        else:
            out[a["player"]] = p + 1
    return out

def getActionsByRound(seats, rounds):
    out = []
    for a in getSortedActions(seats):
        # find out which round we're in
        while len(rounds) > 1 and a["time"] > rounds[1]["time"]:
            # if the above is true, pop the first round off the list
            rounds = rounds[1:]
        a["round"] = rounds[0]["round"] # name
        out.append(a)
    return out

def getSortedActions(seats):
    return sorted(getAllActions(seats), 
        key=lambda x: x["time"])

def getAllActions(seats):
    out = []
    for s in seats:
        for a in s["actions"]:
            if a["amount"] is None:
                a["amount"] = 0 # make not null
            a["player"] = s["name"]
            out.append(a)
    return out

def getHoleCards(seat_data):
    # PROBLEM: when hero folds, their hole cards aren't revealed by getHistory...
    for c in seat_data["cards"]:
        if c["holeCard"] and c["isRevealed"]:
            yield cardModelFromJson(c)

def cardModelFromJson(card_data):
    # on BCP, cards are "HEARTS", "CLUBS" etc.
    # first character is used to map to Suit enum
    return models.PlayingCard.objects.get(
        suit=card_data["suit"][0],
        rank=card_data["rank"])
