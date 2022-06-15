from django.db import models
from django.db.models import Q
from django.db.models import Sum

class Player(models.Model):
    account_number = models.IntegerField(default=0)
    user_name = models.CharField(max_length=200)
    is_hero = models.BooleanField(default=False)

class Table(models.Model):
    name = models.CharField(max_length=200)

class PlayingCard(models.Model):
    suit = models.CharField(max_length=20)
    rank = models.CharField(max_length=2) # 2, 3, ... J, Q, K, A
    rank_integer = models.IntegerField() # 2 ranks 1, A ranks 13

# hand: one hand played at a table
# not one pair of cards held by a player
class Hand(models.Model):
    site_key = models.CharField(max_length=200) # lookup key from site
    table = models.ForeignKey(Table, on_delete=models.CASCADE, default=0)
    time_stamp = models.DateTimeField()
    big_blind = models.IntegerField(default=0)
    flop_cards = models.ManyToManyField(PlayingCard)
    turn_card = models.ForeignKey(PlayingCard, on_delete=models.DO_NOTHING, related_name="turn_cards", null=True)
    river_card = models.ForeignKey(PlayingCard, on_delete=models.DO_NOTHING, related_name="river_cards", null=True)

    def playerCount(self):
        return len(self.seat_set.all())

    def isAnyPlayerAllIn(self):
        return any(s.isAllIn() for s in self.seat_set.all())

# a "hand" in the sense of two cards dealt to a player
class Seat(models.Model):
    player = models.ForeignKey(Player, on_delete=models.CASCADE)
    hand = models.ForeignKey(Hand, on_delete=models.CASCADE)
    hole_cards = models.ManyToManyField(PlayingCard)
    hole_cards_shown = models.BooleanField(default=False)
    is_winner = models.BooleanField(default=False)
    is_big_blind = models.BooleanField(default=False)
    is_small_blind = models.BooleanField(default=False)
    position = models.IntegerField(default=0)
    starting_stack = models.IntegerField(default=0)
    # position convention:
    # increasing integers based on pre-flop betting order
    # 1 = under the gun
    # N = big blind

    def potContributions(self):
        return self.action_set.aggregate(Sum('amount'))["amount__sum"]

    # so far haven't related all-in to an action
    # only to a seat
    def isAllIn(self):
        return self.potContributions() == self.starting_stack

    def allInRound(self):
        # if all-in, returns PREFLOP, FLOP, TURN or RIVER
        # else returns empty string
        if self.isAllIn():
            # if all-in, that bet will be the last action in the hand for this seat
            return self.action_set.order_by('-number')[0].round
        return ""
        
    def isVPIP(self):
        return self.action_set.filter(
            round="PREFLOP").filter(
                Q(type="CALL") | Q(type="RAISE")).count() > 0
    
    def preflopBettorsAfter(self):
        # different convention of position
        # big blind = 0, UTG = N-1
        return self.hand.playerCount() - self.position

    def vpipActionsBefore(self):
        # returns number of pre-flop calls or voluntary bets
        # from seats acting before this one
        # range is 0 to N-1
        # query action number against position+2, since POST_BLINDs are always first two actions
        # even in two-handed games
        return Action.objects.filter(
            seat__hand=self.hand, number__lt=(self.position+2), round="PREFLOP").filter(
                Q(type="CALL") | Q(type="RAISE")).count() # note POST_BLIND is not voluntary     

    def holeCardsString(self):
        if not self.hole_cards_shown:
            return ""
        else:
            cards = self.hole_cards.order_by('-rank_integer').all()
            out = cards[0].rank + cards[1].rank
            if cards[0].rank != cards[1].rank:
                if cards[0].suit == cards[1].suit:
                    out += "s"
                else:
                    out =+ "o"
            return out

class Action(models.Model):
    seat = models.ForeignKey(Seat, on_delete=models.CASCADE)
    type = models.CharField(max_length=10) # POST_BLIND, CHECK, CALL, RAISE, FOLD
    amount = models.IntegerField(default=0)
    round = models.CharField(max_length=20) # PREFLOP, FLOP, TURN, RIVER
    number = models.IntegerField(default=0) # puts actions is sorted order within Hand, starts at 1
