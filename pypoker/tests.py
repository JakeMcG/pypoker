from django.test import TestCase
import json
import core.models as models
from core.interfaces import bcp
from core.analysis import preflop
import itertools
import datetime
import core.views as views

testFiles = {
    "baseline": "hand_baseline.json",
    "big_blind_steal": "hand_bb_steal.json"
}

def loadJsonFromFile(fileName):
    f = open("tests/" + fileName)
    data = json.load(f)
    f.close()
    return data

def populateCardDb():
    models.PlayingCard.objects.all().delete()

    suits = models.PlayingCard.Suit.values
    ranks = ["2", "3", "4", "5", "6", "7", "8", "9", "T", "J", "Q", "K", "A"]
    assert(len(ranks) == 13)

    d = dict()
    for (i,r) in enumerate(ranks):
        d[r] = i+1 # 2 ranks 1, A ranks 13
    assert(d["2"] == 1)
    assert(d["5"] == 4)
    assert(d["A"] == 13)

    for (s, r) in itertools.product(suits, ranks):
        models.PlayingCard.objects.create(suit=s, rank=r, rank_integer=d[r])

def getCardModel(suit, rank):
    return models.PlayingCard.objects.get(suit=suit, rank=rank)

class BcpTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        populateCardDb()

        # the loop below writes hands from testFiles into the test database
        # and stores the associated json in cls.testHands
        # testHands: dict {'name': dict_from_json}
        # keys are same as testFiles
        # use this construct to access different data in different test cases:
        # test_data["baseline"] vs test_data["special_case"]
        cls.testHands = {}
        for (k,v) in testFiles.items():
            cls.testHands[k] = loadJsonFromFile(v)     

            # create hand object
            t = models.Table.objects.create(name=cls.testHands[k]["name"])
            models.Hand.objects.create(
                site_key=cls.testHands[k]["key"],
                table=t,
                time_stamp=datetime.datetime.now()) # timestamp is dummy
            bcp.storeHand(cls.testHands[k])

    def defTestCardDatabase(self):
        self.assertEqual(models.PlayingCard.objects.count(), 52)

    def testCardToModel(self):     
        card = self.testHands["baseline"]["rounds"][1]["community"][0]
        cardModel = bcp.cardModelFromJson(card)

        self.assertEqual(type(cardModel), models.PlayingCard)
        self.assertEqual(cardModel.suit, models.PlayingCard.Suit.CLUBS)
        self.assertEqual(cardModel.rank, "7")
        self.assertEqual(cardModel.rank_integer, 6)

    def testActionsByRound(self):
        actions = bcp.getActionsByRound(
            self.testHands["baseline"]["seats"],
            self.testHands["baseline"]["rounds"])
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

    def testParseDate(self):
        date = views.parseDate("2022-05-15")
        expected = datetime.datetime(2022, 5, 15,
            0, 0, 0, 0)
        self.assertEqual(date, expected)

    def testHand(self):
        # hand-specific fields
        h = models.Hand.objects.get(site_key=self.testHands["baseline"]["key"])

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
    
    def testSeats(self):     
        # seat-specific fields
        h = models.Hand.objects.get(site_key=self.testHands["baseline"]["key"])
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

        self.assertEqual(s[0].isVPIP(), True)
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
        
        self.assertEqual(s[0].isVPIP(), True)
        self.assertEqual(s[0].preflopBettorsAfter(), 4)
        self.assertEqual(s[0].vpipActionsBefore(), 0)
        self.assertEqual(s[0].potContributions(), 2000)
        self.assertEqual(s[0].isAllIn(), False)
        self.assertEqual(s[0].profit(), -2000)

        s = seats.filter(player__user_name="Mike M")
        self.assertEqual(s[0].isVPIP(), False)
        self.assertEqual(s[0].preflopBettorsAfter(), 2)
        self.assertEqual(s[0].vpipActionsBefore(), 2)
        self.assertEqual(s[0].isAllIn(), False)

        s = seats.filter(player__user_name="Phil I")
        self.assertEqual(s[0].holeCardsString(), "QQ")

        s = seats.filter(player__user_name="Daniel N")
        self.assertEqual(s[0].winnings, 10064)
        self.assertEqual(s[0].potContributions(), 5282)
        self.assertEqual(s[0].profit(), 4782)

    def testPreflopStats(self):
        p = models.Player.objects.get(user_name="Phil H")
        vpip = preflop.vpipBySeat(p.seat_set.all())
        self.assertEqual(len(vpip), 1) # assert that big-blind steal is excluded
        vpip = vpip[0]
        self.assertEqual(vpip["starting_stack"], 1041)
        self.assertEqual(vpip["vpip"], True)
        self.assertEqual(vpip["position"], 0)

    def testPositionsForBBSteal(self):
        h = models.Hand.objects.get(site_key=self.testHands["big_blind_steal"]["key"])
        seats = h.seat_set.all()

        for s in seats:
            if s.player.user_name == "Phil H":
                self.assertEqual(s.position, 2)
            elif s.player.user_name == "Tony G":
                self.assertEqual(s.position, 1)
    