from tests import common
import core.models as models
import core.views as views
import datetime, pytz
from django.test import TestCase

class PrimitiveTests(TestCase):
    def testCardDatabase(self):
        common.populateCardDb()
        self.assertEqual(models.PlayingCard.objects.count(), 52)

        AS = models.PlayingCard.objects.get(
            suit=models.PlayingCard.Suit.SPADES,
            rank="A"
        )
        self.assertEqual(AS.rank_integer, 13)

    def testParseDate(self):
        date = views.parseDate("2022-05-15")
        expected = datetime.datetime(2022, 5, 15,
            0, 0, 0, 0, tzinfo=pytz.UTC)
        self.assertEqual(date, expected)   