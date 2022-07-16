from django.test import TestCase
import core.models as models
from core.interfaces import bcp, parser
import datetime
from tests import common

def getCardModel(suit, rank):
    return models.PlayingCard.objects.get(suit=suit, rank=rank)

class BcpTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        common.populateCardDb()
        common.storeTestHandsToDb()

    def testCardToModel(self):     
        card = common.getHandJson("oabw2ys48s")["rounds"][1]["community"][0]
        cardModel = bcp.cardModelFromJson(card)

        self.assertEqual(type(cardModel), models.PlayingCard)
        self.assertEqual(cardModel.suit, models.PlayingCard.Suit.CLUBS)
        self.assertEqual(cardModel.rank, "7")
        self.assertEqual(cardModel.rank_integer, 6)

    def testConvertTime(self):
        time = parser.convertBcpTime("2022-04-02T02:29:25.586Z")
        expected = datetime.datetime(2022, 4, 2,
            2, 29, 25, 586000)
        self.assertEqual(time, expected)

    def testHand(self):
        # hand-specific fields
        h = common.getHandObject("oabw2ys48s")

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
        self.assertEqual(h.player_count, 6)
        self.assertEqual(h.isAnyPlayerAllIn(), True)

    def testPositionsForBBSteal(self):
        h = common.getHandObject("fob3lviaoh")
        seats = h.seat_set.all()

        for s in seats:
            if s.player.user_name == "Phil H":
                self.assertEqual(s.position, 2)
            elif s.player.user_name == "Tony G":
                self.assertEqual(s.position, 1)

    def testAccounting(self):
        # assert that every hands pot contributions as calculated by the parser
        # (from the sum of actions)
        # matches the pot contributions in the json file
        for f in common.testFileNames():
            testHand = common.getHandJson(f)
            h = common.getHandObject(f)

            for testSeat in testHand["seats"]:
                s = h.seat_set.annotated().get(player__user_name=testSeat["name"])
                self.assertEqual(s.pot_contributions, testSeat["potContributions"])
                self.assertEqual(s.winnings, testSeat["winnings"])
                self.assertEqual(s.profit, testSeat["winnings"] - testSeat["potContributions"])
    
    def testSeats(self): 
        # seat-specific fields
        h = common.getHandObject("oabw2ys48s")
        seats = h.seat_set.annotated()

        s = seats.get(player__user_name="Phil H")

        self.assertEqual(s.hole_cards_shown, True)
        self.assertEqual(s.is_winner, False)
        self.assertEqual(s.is_big_blind, True)
        self.assertEqual(s.is_small_blind, False)
        self.assertEqual(s.position, 6)
        hole_cards = s.hole_cards.all()
        self.assertEqual(len(hole_cards), 2)
        self.assertTrue(getCardModel("D", "A") in hole_cards)
        self.assertTrue(getCardModel("D", "2") in hole_cards)
        self.assertEqual(s.holeCardsString(), "A2s")

        self.assertEqual(s.preflopBettorsAfter(), 0)
        self.assertEqual(s.vpipActionsBefore(), 3)
        self.assertEqual(s.starting_stack, 641)
        self.assertEqual(s.is_all_in, True)

        s = seats.get(player__user_name="Doyle B")

        self.assertEqual(s.hole_cards_shown, False)
        self.assertEqual(s.is_winner, False)
        self.assertEqual(s.is_big_blind, False)
        self.assertEqual(s.is_small_blind, False)
        self.assertEqual(s.position, 2)
        self.assertEqual(s.starting_stack, 9775)
        hole_cards = s.hole_cards.all()
        self.assertEqual(len(hole_cards), 0)
        self.assertEqual(s.holeCardsString(), "")
        
        self.assertEqual(s.preflopBettorsAfter(), 4)
        self.assertEqual(s.vpipActionsBefore(), 0)
        self.assertEqual(s.is_all_in, False)

        s = seats.get(player__user_name="Mike M")
        self.assertEqual(s.preflopBettorsAfter(), 2)
        self.assertEqual(s.vpipActionsBefore(), 2)
        self.assertEqual(s.is_all_in, False)

        s = seats.get(player__user_name="Phil I")
        self.assertEqual(s.holeCardsString(), "QQ")
            