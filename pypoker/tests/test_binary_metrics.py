from django.test import TestCase
import core.models as models
from tests import common
from core.analysis import seat_metrics

Type = models.BinarySeatMetric.Metric

def getMetric(hand, userName, metric):
    return models.BinarySeatMetric.objects.get(
        seat__hand__site_key=common.getHandJson(hand)["key"],
        seat__player__user_name=userName,
        type=metric
    )

class SeatMetricTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        common.populateCardDb()
        common.storeTestHandsToDb()

        for s in models.Seat.objects.all():
            seat_metrics.update_metrics(s)

    def testVPIP(self):
        vpip = getMetric("oabw2ys48s", "Phil H", Type.VPIP)
        self.assertEqual(vpip.value, True)
        self.assertEqual(vpip.eligibility, True)

        vpip = getMetric("oabw2ys48s", "Tony G", Type.VPIP)
        self.assertEqual(vpip.value, False)
        self.assertEqual(vpip.eligibility, True)

        vpip = getMetric("fob3lviaoh", "Phil H", Type.VPIP)
        self.assertEqual(vpip.value, False)
        self.assertEqual(vpip.eligibility, False)

    def testPFR(self):
        pfr = getMetric("oabw2ys48s", "Tony G", Type.PREFLOP_RAISE)
        self.assertEqual(pfr.value, False)
        self.assertEqual(pfr.eligibility, True)
    
        pfr = getMetric("oabw2ys48s", "Doyle B", Type.PREFLOP_RAISE)
        self.assertEqual(pfr.value, True)
        self.assertEqual(pfr.eligibility, True)

        pfr = getMetric("oabw2ys48s", "Phil I", Type.PREFLOP_RAISE)
        self.assertEqual(pfr.value, True)
        self.assertEqual(pfr.eligibility, True)

    def test3Bet(self):
        bet3 = getMetric("oabw2ys48s", "Tony G", Type.PREFLOP_3BET)
        self.assertEqual(bet3.value, False)
        self.assertEqual(bet3.eligibility, False)
    
        bet3 = getMetric("oabw2ys48s", "Doyle B", Type.PREFLOP_3BET)
        self.assertEqual(bet3.value, False)
        self.assertEqual(bet3.eligibility, False)

        bet3 = getMetric("oabw2ys48s", "Phil I", Type.PREFLOP_3BET)
        self.assertEqual(bet3.value, True)
        self.assertEqual(bet3.eligibility, True)
    