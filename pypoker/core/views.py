import datetime
from django.http import JsonResponse
from django.shortcuts import render
from .interfaces import bcp
import core.models as models
from .analysis import preflop as pf
import json

def getHero():
    return models.Player.objects.get(is_hero=True)

def parseDate(dateStr):
    return datetime.datetime.strptime(dateStr,
        "%Y-%m-%d")

def filterSeats(player, filters):
    # corresponds to front-end hand filter
    out = player.seat_set.all()
    if filters["min-date"] != "":
        out = out.filter(hand__time_stamp__gt=parseDate(filters["min-date"]))
    if filters["max-date"] != "":
        out = out.filter(hand__time_stamp__lt=parseDate(filters["max-date"]))
    if filters["min-bb"] != "":
        out = out.filter(hand__big_blind__gt=filters["min-bb"])
    if filters["max-bb"] != "":
        out = out.filter(hand__big_blind__lt=filters["max-bb"])
    return out

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
        # populate context
        hero = getHero()
        seats = filterSeats(hero, request.POST)
        response = pf.vpipBySeat(seats)
        return JsonResponse(response, status=200, safe=False)
    # else render the page
    return render(request, "preflop.html")