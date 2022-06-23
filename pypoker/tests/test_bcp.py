from django.test import TestCase
import core.models as models
from core.interfaces import bcp
import datetime
from tests import common

def getCardModel(suit, rank):
    return models.PlayingCard.objects.get(suit=suit, rank=rank)

class BcpTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        common.populateCardDb()
        common.storeTestHandsToDb()

        # make json available for subsequent tests
        cls.baselineHand = common.getHandJson("baseline")
        cls.bbStealHand = common.getHandJson("big_blind_steal")

    def testCardToModel(self):     
        card = self.baselineHand["rounds"][1]["community"][0]
        cardModel = bcp.cardModelFromJson(card)

        self.assertEqual(type(cardModel), models.PlayingCard)
        self.assertEqual(cardModel.suit, models.PlayingCard.Suit.CLUBS)
        self.assertEqual(cardModel.rank, "7")
        self.assertEqual(cardModel.rank_integer, 6)

    def testActionsByRound(self):
        actions = bcp.getActionsByRound(
            self.baselineHand["seats"],
            self.baselineHand["rounds"])
        expected = [
            {'amount': 400, 'type': 'POST_BLIND', 'player': 'Phil H', 'round': 'PREFLOP'}, 
            {'amount': 200, 'type': 'POST_BLIND', 'player': 'Daniel N', 'round': 'PREFLOP'}, 
            {'amount': 0, 'type': 'FOLD', 'player': 'Tony G', 'round': 'PREFLOP'}, 
            {'amount': 800, 'type': 'RAISE', 'player': 'Doyle B', 'round': 'PREFLOP'}, 
            {'amount': 1200, 'type': 'RAISE', 'player': 'Phil I', 'round': 'PREFLOP'}, 
            {'amount': 0, 'type': 'FOLD','player': 'Mike M', 'round': 'PREFLOP'}, 
            {'amount': 1200, 'type': 'CALL', 'player': 'Daniel N', 'round': 'PREFLOP'}, 
            {'amount': 641, 'type': 'CALL', 'player': 'Phil H', 'round': 'PREFLOP'}, 
            {'amount': 1200, 'type': 'CALL', 'player': 'Doyle B', 'round': 'PREFLOP'}, 
            {'amount': 0, 'type': 'CHECK', 'player': 'Daniel N', 'round': 'FLOP'}, 
            {'amount': 0, 'type': 'CHECK', 'player': 'Doyle B', 'round': 'FLOP'}, 
            {'amount': 1941, 'type': 'RAISE', 'player': 'Phil I', 'round': 'FLOP'}, 
            {'amount': 3882, 'type': 'RAISE', 'player': 'Daniel N', 'round': 'FLOP'}, 
            {'amount': 0, 'type': 'FOLD', 'player': 'Doyle B', 'round': 'FLOP'}]
        for (n,e) in enumerate(expected):
            for (k,v) in e.items():
                self.assertEqual(v, actions[n][k])

    def testConvertTime(self):
        time = bcp.convertBcpTime("2022-04-02T02:29:25.586Z")
        expected = datetime.datetime(2022, 4, 2,
            2, 29, 25, 586000)
        self.assertEqual(time, expected)

    def testHand(self):
        # hand-specific fields
        h = models.Hand.objects.get(site_key=self.baselineHand["key"])

        self.assertEqual(h.big_blind, 400)

        flop_cards = h.flop_cards.all()
        self.assertEqual(len(flop_cards), 3)
        self.assertTrue(getCardModel("C", "7") in flop_cards)
        self.assertTrue(getCardModel("S", "4") in flop_cards)
        self.assertTrue(getCardModel("D", "K") in flop_cards)
        self.assertEqual(h.turn_card, getCardModel("H", "4"))
        self.assertEqual(h.river_card, getCardModel("S", "9"))

        seats = h.seat_set.all()
        self.assertEqual(len(seats), 6)
        self.assertEqual(h.playerCount(), 6)
        self.assertEqual(h.isAnyPlayerAllIn(), True)

    def testPositionsForBBSteal(self):
        h = models.Hand.objects.get(site_key=self.bbStealHand["key"])
        seats = h.seat_set.all()

        for s in seats:
            if s.player.user_name == "Phil H":
                self.assertEqual(s.position, 2)
            elif s.player.user_name == "Tony G":
                self.assertEqual(s.position, 1)
    
    def testSeats(self):     
        # seat-specific fields
        h = models.Hand.objects.get(site_key=self.baselineHand["key"])
        seats = h.seat_set.all()

        s = seats.filter(player__user_name="Phil H")
        self.assertEqual(len(s), 1)

        self.assertEqual(s[0].hole_cards_shown, True)
        self.assertEqual(s[0].is_winner, False)
        self.assertEqual(s[0].is_big_blind, True)
        self.assertEqual(s[0].is_small_blind, False)
        self.assertEqual(s[0].position, 6)
        self.assertEqual(s[0].starting_stack, 1041)
        self.assertEqual(s[0].winnings, 0)
        hole_cards = s[0].hole_cards.all()
        self.assertEqual(len(hole_cards), 2)
        self.assertTrue(getCardModel("D", "A") in hole_cards)
        self.assertTrue(getCardModel("D", "2") in hole_cards)
        self.assertEqual(s[0].holeCardsString(), "A2s")

        self.assertEqual(s[0].preflopBettorsAfter(), 0)
        self.assertEqual(s[0].vpipActionsBefore(), 3)
        self.assertEqual(s[0].potContributions(), 1041)
        self.assertEqual(s[0].isAllIn(), True)
        self.assertEqual(s[0].allInRound(), models.Action.Round.PREFLOP)
        self.assertEqual(s[0].profit(), -1041)

        s = seats.filter(player__user_name="Doyle B")
        self.assertEqual(len(s), 1)

        self.assertEqual(s[0].hole_cards_shown, False)
        self.assertEqual(s[0].is_winner, False)
        self.assertEqual(s[0].is_big_blind, False)
        self.assertEqual(s[0].is_small_blind, False)
        self.assertEqual(s[0].position, 2)
        self.assertEqual(s[0].starting_stack, 10575)
        hole_cards = s[0].hole_cards.all()
        self.assertEqual(len(hole_cards), 0)
        self.assertEqual(s[0].holeCardsString(), "")
        self.assertEqual(s[0].winnings, 0)
        
        self.assertEqual(s[0].preflopBettorsAfter(), 4)
        self.assertEqual(s[0].vpipActionsBefore(), 0)
        self.assertEqual(s[0].potContributions(), 2000)
        self.assertEqual(s[0].isAllIn(), False)
        self.assertEqual(s[0].profit(), -2000)

        s = seats.filter(player__user_name="Mike M")
        self.assertEqual(s[0].preflopBettorsAfter(), 2)
        self.assertEqual(s[0].vpipActionsBefore(), 2)
        self.assertEqual(s[0].isAllIn(), False)

        s = seats.filter(player__user_name="Phil I")
        self.assertEqual(s[0].holeCardsString(), "QQ")

        s = seats.filter(player__user_name="Daniel N")
        self.assertEqual(s[0].winnings, 10064)
        self.assertEqual(s[0].potContributions(), 5282)
        self.assertEqual(s[0].profit(), 4782)    
    