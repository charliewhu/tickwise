from django.http import HttpRequest
from django.shortcuts import render
from src.data import models
from src import services


def index(request: HttpRequest):
    context = {
        "stats": services.get_trade_summary_stats(),
        "trades": models.Trade.objects.all(),
    }

    return render(request, "index.html", context)
