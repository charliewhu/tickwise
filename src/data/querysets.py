import typing as t
import decimal

from django.db import models
from django.db.models.functions import TruncDate, Round

if t.TYPE_CHECKING:
    from .models import Trade  # noqa: F401


class TradeQueryset(models.QuerySet["Trade"]):
    # summary statistics

    def get_total_return(self):
        return round(
            self.exclude(exit_price__isnull=True).aggregate(
                models.Sum("actual_r", default=0)
            )["actual_r__sum"],
            2,
        )

    def get_win_count(self):
        return self.filter(actual_r__gt=0).count()

    def get_loss_count(self):
        return self.filter(actual_r__lte=0).count()

    def get_strike_rate(self):
        try:
            return round(decimal.Decimal(self.get_win_count() / self.count()), 3)
        except ZeroDivisionError:
            return 0

    def get_average_planned_r(self):
        try:
            return round(
                self.aggregate(models.Sum("planned_r", default=0))["planned_r__sum"]
                / self.count(),
                2,
            )

        except (ZeroDivisionError, decimal.InvalidOperation):
            return 0

    def get_average_trade(self):
        if count := self.count():
            return self.get_total_return() / count

        return 0

    def get_average_winner(self):
        win_count = self.filter(is_winner=True).count()
        if not win_count:
            return 0

        return (
            round(
                self.exclude(exit_price__isnull=True)
                .filter(is_winner=True)
                .aggregate(models.Sum("actual_r", default=0))["actual_r__sum"],
                2,
            )
            / win_count
        )

    def get_average_loser(self):
        loss_count = self.filter(is_winner=False).count()
        if not loss_count:
            return 0

        return (
            round(
                self.exclude(exit_price__isnull=True)
                .filter(is_winner=False)
                .aggregate(models.Sum("actual_r", default=0))["actual_r__sum"],
                2,
            )
            / loss_count
        )

    def get_profit_factor(self):
        try:
            return decimal.Decimal(
                round(abs(self.get_average_winner() / self.get_average_loser()), 2)
            )
        except ZeroDivisionError:
            return None

    def get_expectancy(self):
        if (profit_factor := self.get_profit_factor()) is None:
            return self.get_average_trade()

        return round(profit_factor * self.get_strike_rate() - 1, 2)

    def get_winning_days_count(self):
        return self.list_total_r_by_day().filter(total_r__gt=0).count()

    def get_losing_days_count(self):
        return self.list_total_r_by_day().filter(total_r__lte=0).count()

    def get_total_trading_days_count(self):
        return (
            self.annotate(day=TruncDate("entered_at")).values("day").distinct().count()
        )

    def get_average_trading_day_r(self):
        try:
            return self.get_total_return() / self.get_total_trading_days_count()
        except decimal.InvalidOperation:
            return 0

    def get_winning_days_percent(self):
        try:
            return round(
                (self.get_winning_days_count() / self.get_total_trading_days_count())
                * 100,
                1,
            )
        except ZeroDivisionError:
            return 0

    def get_max_consecutive_winners(self):
        transactions = self.order_by("exited_at").values_list("actual_r", flat=True)

        max_streak = 0
        current_streak = 0

        for actual_r in transactions:
            current_streak = current_streak + 1 if actual_r > 0 else 0
            max_streak = max(max_streak, current_streak)

        return max_streak

    def get_max_consecutive_losers(self):
        transactions = self.order_by("exited_at").values_list("actual_r", flat=True)

        max_streak = 0
        current_streak = 0

        for actual_r in transactions:
            current_streak = current_streak + 1 if actual_r <= 0 else 0
            max_streak = max(max_streak, current_streak)

        return max_streak

    # list objects
    def list_total_r_by_day(self):
        qs = (
            self.annotate(day=TruncDate("entered_at"))
            .values("day")
            .annotate(total_r=Round(models.Sum("actual_r", default=0), 2))
            .order_by("day")
        )
        return qs


TradeManager = models.Manager.from_queryset(TradeQueryset)
