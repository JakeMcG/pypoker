from django.contrib import admin

from .models import *

admin.site.register([Player, Table, Hand, PlayingCard, Seat])
