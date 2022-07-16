import datetime

# stack in BCP response appears to be after pot contributions but before winnings
def getStartingStack(seat):
    return seat["stack"] + seat["potContributions"]

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

# this function is needed because action amounts are not incremental
# a raise followed by another raise do not sum to the amount needed to call thereafter
# this is contrary to the convention followed in pypoker's database
def correctActionAmounts(actions):
    lastRound = "PREFLOP"
    lastAmount = {} # dict: last action in a given round indexed by player
    
    for a in actions:
        if a["round"] != lastRound:
            lastAmount = {} # reset accounting each round
        lastRound = a["round"]
        if a["type"] == "CHECK" or a["type"] == "FOLD":
            continue

        total = a["amount"] # total amount, uncorrected
        a["amount"] -= lastAmount.get(a["player"], 0) # correct by previously committed amount
        lastAmount[a["player"]] = total 
    
    return actions

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



