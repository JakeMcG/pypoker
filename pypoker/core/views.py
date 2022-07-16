import datetime, pytz
from django.http import JsonResponse
from django.shortcuts import render
from django.db.models import Sum, F
from .interfaces import bcp
import core.models as models
from .analysis import seat_metrics

def getHeroSeats():
    return models.Seat.objects.annotated().filter(player__is_hero=True)

def refreshMetrics(seats):
    for s in seats.filter(metrics_fresh=False):
        seat_metrics.update_metrics(s)

def parseDate(dateStr):
    return datetime.datetime.strptime(dateStr,
        "%Y-%m-%d").replace(tzinfo=pytz.UTC)

def filterByDateAndBigBlind(seats, filters):
    # corresponds to front-end hand filter
    if filters.get("min-date", "") != "":
        seats = seats.filter(hand__played_time__gte=parseDate(filters["min-date"]))
    if filters.get("max-date", "") != "":
        seats = seats.filter(hand__played_time__lte=parseDate(filters["max-date"]))
    if filters.get("min-bb", "") != "":
        seats = seats.filter(hand__big_blind__gte=filters["min-bb"])
    if filters.get("max-bb", "") != "":
        seats = seats.filter(hand__big_blind__lte=filters["max-bb"])
    return seats

def index(request):
    return render(request, "index.html")

def retrieve(request):
    # if ajax POST request, it's a request to import new hands
    if request.is_ajax and request.method == "POST":
        username = request.POST["username"]
        password = request.POST["password"]
        result = bcp.loadRecentHandsToDb(username, password)
        status = 200 # not sure what to set here
        return JsonResponse(result, 
                            status=status)
    # else it's a request to render the retrieve page
    return render(request, "retrieve.html")

def preflop(request):
    # preflop data is requested via ajax POST request
    if request.is_ajax and request.method == "POST":
        seats = filterByDateAndBigBlind(getHeroSeats(), request.POST)

        refreshMetrics(seats)

        response = []
        for s in seats:
            el = {}
            vpip = s.getMetric(models.BinarySeatMetric.Metric.VPIP)
            if not vpip.eligibility:
                continue
            el["starting_stack"] = s.starting_stack
            el["position"] = s.preflopBettorsAfter()
            el["big_blind"] = s.hand.big_blind
            el["vpip"] = vpip.value
            el["vp_before"] = s.vpipActionsBefore()
            response.append(el)
        return JsonResponse(response, status=200, safe=False)
    # else render the page
    return render(request, "preflop.html")

def outcomes(request):
    context = {
        "metrics": {
            "Pre-flop": {
                "vpip": "VPIP",
                "pfr": "Raise",
                "3bet": "3-Bet"
            },
            "Flop": {
                "fcbet": "Cont. Bet"
            }
        }        
    } # available metrics by round, with labels
    # when filter is refreshed: AJAX POST request
    if request.is_ajax and request.method == "POST":
        Type = models.BinarySeatMetric.Metric
        mapping = {
            "vpip": Type.VPIP,
            "pfr": Type.PREFLOP_RAISE,
            "3bet": Type.PREFLOP_3BET
        } # maps form field names to metrics
        seats = filterByDateAndBigBlind(getHeroSeats(), request.POST)
        refreshMetrics(seats)

        eligibleSeats = seats
        matchedSeats = seats
        for (key, metric) in mapping.items():
            if request.POST.get(key, "") == "on": # selected in view
                eligibleSeats = eligibleSeats.filter(
                    metrics__type=metric, metrics__eligibility=True)
                matchedSeats = matchedSeats.filter(
                    metrics__type=metric, metrics__value=True)

        response = {
            "totalCount": seats.count(),
            "eligibleCount": eligibleSeats.count(),
            "matchedCount": matchedSeats.count(),
            "matchedWins": matchedSeats.filter(is_winner=True).count(),
            "matchedProfit": matchedSeats.aggregate(Sum("profit"))["profit__sum"],
            "matchedProfitBB": matchedSeats.aggregate(Sum("profit_bb"))["profit_bb__sum"]
        }

        return JsonResponse(response, status=200)
    return render(request, "outcomes.html", context=context)
