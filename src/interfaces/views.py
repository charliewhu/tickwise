from django.http import HttpRequest
from django.shortcuts import render
from src.data import models


def index(request: HttpRequest):
    context = {
        "trade_count": models.Trade.objects.count(),
        "total_return": models.Trade.objects.get_total_return(),
        "win_count": models.Trade.objects.get_win_count(),
        "loss_count": models.Trade.objects.get_loss_count(),
        "strike_rate": round(models.Trade.objects.get_strike_rate() * 100, 1),
        "average_trade": models.Trade.objects.get_average_trade(),
        "average_winner": models.Trade.objects.get_average_winner(),
        "average_loser": models.Trade.objects.get_average_loser(),
        "average_planned_r": models.Trade.objects.get_average_planned_r(),
        "expectancy": models.Trade.objects.get_expectancy(),
        "average_trading_day_r": models.Trade.objects.get_average_trading_day_r(),
        "profit_factor": models.Trade.objects.get_profit_factor(),
        "winning_days_count": models.Trade.objects.get_winning_days_count(),
        "losing_days_count": models.Trade.objects.get_losing_days_count(),
        "winning_day_percent": models.Trade.objects.get_winning_days_percent(),
        "max_consecutive_winners": models.Trade.objects.get_max_consecutive_winners(),
        "max_consecutive_losers": models.Trade.objects.get_max_consecutive_losers(),
        "current_balance": models.Account.objects.get(pk=1).get_current_balance(),
        "trades": models.Trade.objects.all(),
    }

    return render(request, "index.html", context)
