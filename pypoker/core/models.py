from django.db import models
from django.db.models import Q, F, Sum, Count, ExpressionWrapper

class Player(models.Model):
    account_number = models.IntegerField(default=0)
    user_name = models.CharField(max_length=200)
    is_hero = models.BooleanField(default=False)

class Table(models.Model):
    name = models.CharField(max_length=200)

class PlayingCard(models.Model):
    class Suit(models.TextChoices):
        SPADES = "S"
        HEARTS = "H"
        DIAMONDS = "D"
        CLUBS = "C"

    suit = models.CharField(max_length=1, 
        choices=Suit.choices, 
        default=Suit.SPADES)
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
    
    class HandManager(models.Manager):
        def annotated(self):
            return self.annotate(
                player_count=Count('seat'),
            )
    objects = HandManager()

    def isAnyPlayerAllIn(self):
        return self.seat_set.annotated().filter(is_all_in=True).count() > 0

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
    winnings = models.IntegerField(default=0)
    metrics_fresh = models.BooleanField(default=False)
    # position convention:
    # increasing integers based on pre-flop betting order
    # 1 = under the gun
    # N = big blind

    class SeatManager(models.Manager):
        def annotated(self):
            return self.annotate(
                pot_contributions=Sum('action__amount'),
                profit=F('winnings')-F('pot_contributions'),
                profit_bb=ExpressionWrapper(
                    F('profit')*1.0/F('hand__big_blind'), # 1.0 avoids rounding in DB
                    output_field=models.FloatField()),
                is_all_in=ExpressionWrapper(
                    Q(pot_contributions=F('starting_stack')),
                    output_field=models.BooleanField()),
            )
    objects = SeatManager() # manager

    def getMetric(self, metric):
        return self.metrics.get(type=metric)
        
    def preflopBettorsAfter(self):
        # different convention of position
        # big blind = 0, UTG = N-1
        return self.hand.seat_set.count() - self.position

    def vpipActionsBefore(self):
        # returns number of pre-flop calls or voluntary bets (not blinds)
        # from seats acting before this one
        # range is 0 to N-1
        # query on position+2 because first two actions are blinds
        return self.allActionsInHand().filter(
                number__lt=(self.position+2), round=Action.Round.PREFLOP
            ).filter(
                Q(type=Action.Type.CALL) | Q(type=Action.Type.RAISE)
            ).count() 

    def allActionsInHand(self):
        return Action.objects.filter(seat__hand=self.hand).order_by('number')

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
    class Type(models.TextChoices):
        BLIND = "B"
        FOLD = "F"
        CHECK = "K"
        CALL = "C"
        RAISE = "R"

    class Round(models.TextChoices):
        BLINDS = "B" # posting blinds belongs to this, not preflop
        PREFLOP = "P"
        FLOP = "F"
        TURN = "T"
        RIVER = "R"

    seat = models.ForeignKey(Seat, on_delete=models.CASCADE)
    type = models.CharField(max_length=1,
        choices=Type.choices,
        default=Type.CHECK)
    amount = models.IntegerField(default=0)
    round = models.CharField(max_length=1,
        choices=Round.choices,
        default=Round.PREFLOP)
    number = models.IntegerField(default=0) # puts actions is sorted order within Hand, starts at 1

class BinarySeatMetric(models.Model):
    class Metric(models.IntegerChoices):
        VPIP = 1
        PREFLOP_RAISE = 2
        PREFLOP_3BET = 3
        PREFLOP_ALLIN = 4

    seat = models.ForeignKey(Seat, on_delete=models.CASCADE, related_name="metrics")
    type = models.IntegerField(choices=Metric.choices)
    eligibility = models.BooleanField(default=False)
    value = models.BooleanField(default=False)
