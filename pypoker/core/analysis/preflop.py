import core.models as models

# TODO:
# some positions return -1
# I think this is when sitting out
# look into this, add is_sitting_in if possible
# or this may be in a 2 player game when UTG folds
# yes this is the problem, in bcp.getPlayerPositions()
# add a hand with a big-blind win to tests
# fix: if getPlayerPositions returns fewer than N entries
# set Seat()

def vpipBySeat(seats):
    # seats: a queryset over the Seat mode
    # returns list of dicts
    # each dict is a hand
    # {timestamp, big_bling (amount), starting_stack, vp (boolean), position (bettors after), is_big_blind, is_small_blind}
    out = []
    seats = seats.order_by("-hand__time_stamp")
    for seat in seats:
        entry = {}
        entry["starting_stack"] = seat.starting_stack
        entry["position"] = seat.preflopBettorsAfter()
        entry["vpip"] = seat.isVPIP()

        hand = seat.hand
        entry["time_stamp"] = hand.time_stamp
        entry["big_blind"] = hand.big_blind
        entry["num_players"] = hand.playerCount()

        entry["vp_before"] = seat.vpipActionsBefore()

        # when in the big-blind position and with no actions before
        # the player has no option to voluntarily bet
        # these hands should be excluded
        if entry["position"] == 0 and entry["vp_before"] == 0:
            continue

        out.append(entry)
    return out
