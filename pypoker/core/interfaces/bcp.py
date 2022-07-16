import datetime, pytz
import core.models as models
from . import network, parser

FORCE_CREATE = False

_bcp_actions = ["POST_BLIND", "FOLD", "CHECK", "CALL", "RAISE"]
ACTION_MAPPING = dict(zip(
    _bcp_actions, models.Action.Type.values
))
_bcp_rounds = ["", "PREFLOP", "FLOP", "TURN", "RIVER"]
ROUND_MAPPING = dict(zip(
    _bcp_rounds, models.Action.Round.values
))

def loadRecentHandsToDb(username, password):
    result = {
        "error": False,
        "errorText": "",
        "newHands": 0,
        "earliestHandTime": "", # call lastest/earliest to avoid confusion, since later hands loaded first
        "latestHandTime": ""} # result of import to feed to front-end
    
    try:
        with network.BcpSocketInterface() as socket:
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
                        played_time=parser.convertBcpTime(hh["timestamp"]))
                    
                    if h[1] or FORCE_CREATE:
                        # this means a new hand has been created    
                        h[0].imported_time = datetime.datetime.utcnow().replace(tzinfo=pytz.UTC)
                        h[0].save()
                                
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
        result["error"] = True
        result["errorText"] = str(e)
    
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
            starting_stack=parser.getStartingStack(seat),
            winnings=seat["winnings"]
        )
        # Note: seat["stack"] is at END of hand
        for c in getHoleCards(seat):
            # if no hole cards revealed, this loop won't run
            s.hole_cards.add(c)
            s.hole_cards_shown = True
        s.save()

    # store actions
    actions = parser.getActionsByRound(hand["seats"], hand["rounds"])
    actions = parser.correctActionAmounts(actions) # refactoring to come
    # list of dicts, augmented version of bcp actions
    for (n,a) in enumerate(actions):
        if a["type"] == "POST_BLIND":
            round = models.Action.Round.BLINDS
        else:
            round = ROUND_MAPPING[a["round"]]
        
        models.Action.objects.create(
            seat=models.Seat.objects.get(
                hand=h,
                player__user_name=a["player"]),
            type=ACTION_MAPPING[a["type"]],
            amount=a["amount"],
            round=round,
            number=n+1)

    # store player positions
    for (player,pos) in parser.getPlayerPositions(actions).items():
        models.Seat.objects.filter(
            hand=h,
            player__user_name=player).update(
            position=pos)

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