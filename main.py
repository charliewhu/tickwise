from decimal import Decimal
import typing as t

from django.contrib import admin
from django.db import models
from django.db.models.functions import TruncDate, Round
from django.http import HttpRequest
from django.shortcuts import render


from nanodjango import Django

if t.TYPE_CHECKING:
    # This doesn't really exists on django so it always need to be imported this way
    from django.db.models.manager import RelatedManager

app = Django(ADMIN_URL="admin/")


class Ticker(models.Model):
    name = models.CharField(max_length=10)

    if t.TYPE_CHECKING:
        trades = RelatedManager["Trade"]()

    def __str__(self) -> str:
        return self.name


@admin.register(Ticker)
class TickerAdmin(admin.ModelAdmin):
    pass


class Timeframe(models.Model):
    name = models.CharField(max_length=10)

    if t.TYPE_CHECKING:
        trades = RelatedManager["Trade"]()

    def __str__(self) -> str:
        return self.name


@admin.register(Timeframe)
class TimeframeAdmin(admin.ModelAdmin):
    pass


class TradeQueryset(models.QuerySet["Trade"]):
    def get_win_count(self):
        return self.filter(actual_r__gt=0).count()

    def get_loss_count(self):
        return self.filter(actual_r__lte=0).count()

    def get_strike_rate(self):
        return round(Decimal(self.get_win_count() / self.count()), 3)

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

    def get_expectancy(self):
        return round(
            self.get_strike_rate() * self.get_average_winner()
            + (1 - self.get_strike_rate()) * self.get_average_loser(),
            2,
        )

    def get_winning_days_count(self):
        return self.get_r_per_day().filter(total_r__gt=0).count()

    def get_losing_days_count(self):
        return self.get_r_per_day().filter(total_r__lte=0).count()

    def get_total_trading_days_count(self):
        return (
            self.annotate(day=TruncDate("entered_at")).values("day").distinct().count()
        )

    def get_winning_days_percent(self):
        return round(
            (self.get_winning_days_count() / self.get_total_trading_days_count()) * 100,
            1,
        )

    def get_r_per_day(self):
        qs = (
            self.annotate(day=TruncDate("entered_at"))
            .values("day")
            .annotate(total_r=Round(models.Sum("actual_r", default=0), 2))
            .order_by("day")
        )
        return qs


class Trade(models.Model):
    GRADE_CHOICES = [
        ("a", "A"),
        ("b", "B"),
        ("c", "C"),
    ]

    ticker = models.ForeignKey(
        Ticker,
        on_delete=models.SET_NULL,
        null=True,
        related_name="trades",
    )
    long_short_flag = models.CharField(
        max_length=5,
        choices=[("LONG", "Long"), ("SHORT", "Short")],
    )
    trigger_timeframe = models.ForeignKey(
        Timeframe,
        on_delete=models.SET_NULL,
        null=True,
        related_name="trades",
    )

    entered_at = models.DateTimeField()
    exited_at = models.DateTimeField(blank=True, null=True)

    entry_price = models.DecimalField(max_digits=12, decimal_places=5)
    stop_price = models.DecimalField(max_digits=12, decimal_places=5)
    target_price = models.DecimalField(max_digits=12, decimal_places=5)
    exit_price = models.DecimalField(
        max_digits=12,
        decimal_places=5,
        blank=True,
        null=True,
    )

    entry_grade = models.CharField(
        max_length=1,
        choices=GRADE_CHOICES,
        null=True,
        blank=True,
    )
    exit_grade = models.CharField(
        max_length=1,
        choices=GRADE_CHOICES,
        null=True,
        blank=True,
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # generated fields
    planned_r = models.GeneratedField(  # type: ignore
        expression=models.Case(
            models.When(
                models.Q(long_short_flag__exact="LONG"),
                then=(models.F("target_price") - models.F("entry_price"))
                / (models.F("entry_price") - models.F("stop_price")),
            ),
            models.When(
                models.Q(long_short_flag__exact="SHORT"),
                then=(models.F("entry_price") - models.F("target_price"))
                / (models.F("stop_price") - models.F("entry_price")),
            ),
            default=None,
            output_field=models.BooleanField(),
        ),
        output_field=models.DecimalField(
            null=True,
            max_digits=4,
            decimal_places=2,
        ),
        db_persist=False,
    )

    actual_r = models.GeneratedField(  # type: ignore
        expression=models.Case(
            models.When(
                models.Q(long_short_flag__exact="LONG"),
                then=(models.F("exit_price") - models.F("entry_price"))
                / (models.F("entry_price") - models.F("stop_price")),
            ),
            models.When(
                models.Q(long_short_flag__exact="SHORT"),
                then=(models.F("entry_price") - models.F("exit_price"))
                / (models.F("stop_price") - models.F("entry_price")),
            ),
            default=0,
            output_field=models.DecimalField(
                null=True,
                max_digits=4,
                decimal_places=2,
            ),
        ),
        output_field=models.DecimalField(
            null=True,
            max_digits=4,
            decimal_places=2,
        ),
        db_persist=False,
    )

    is_winner = models.GeneratedField(  # type: ignore
        expression=models.Case(
            models.When(
                models.Q(long_short_flag__exact="LONG"),
                then=models.Q(exit_price__gt=models.F("entry_price")),
            ),
            models.When(
                models.Q(long_short_flag__exact="SHORT"),
                then=models.Q(exit_price__lt=models.F("entry_price")),
            ),
            default=None,
            output_field=models.BooleanField(),
        ),
        output_field=models.BooleanField(),
        db_persist=False,
    )

    objects: TradeQueryset = TradeQueryset.as_manager()  # type: ignore

    class Meta:  # type: ignore
        constraints = [
            models.CheckConstraint(
                check=(
                    models.Q(long_short_flag__iexact="SHORT")
                    | models.Q(entry_price__gt=models.F("stop_price"))
                ),
                name="check_valid_long_entry_and_stop_price",
                violation_error_message="Entry price must be greater than stop loss price",
            ),
            models.CheckConstraint(
                check=(
                    models.Q(long_short_flag__iexact="SHORT")
                    | models.Q(target_price__gt=models.F("entry_price"))
                ),
                name="check_valid_long_entry_and_target_price",
                violation_error_message="Target price must be greater than entry price",
            ),
            models.CheckConstraint(
                check=(
                    models.Q(long_short_flag__iexact="LONG")
                    | models.Q(entry_price__lt=models.F("stop_price"))
                ),
                name="check_valid_short_entry_and_stop_price",
                violation_error_message="Entry price must be less than stop loss price",
            ),
            models.CheckConstraint(
                check=(
                    models.Q(long_short_flag__iexact="LONG")
                    | models.Q(target_price__lt=models.F("entry_price"))
                ),
                name="check_valid_short_entry_and_target_price",
                violation_error_message="Target price must be less than entry price",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.long_short_flag} {self.ticker} at {self.entered_at.strftime('%H:%M-%d/%m/%Y')}"

    @property
    def is_long(self):
        return self.long_short_flag == "LONG"


@admin.register(Trade)
class TradeAdmin(admin.ModelAdmin):
    readonly_fields = [
        "planned_r",
        "actual_r",
        "is_winner",
    ]


@app.route("/")
def index(request: HttpRequest):
    context = {
        "trade_count": Trade.objects.count(),
        "win_count": Trade.objects.get_win_count(),
        "loss_count": Trade.objects.get_loss_count(),
        "strike_rate": round(Trade.objects.get_strike_rate() * 100, 1),
        "average_winner": Trade.objects.get_average_winner(),
        "average_loser": Trade.objects.get_average_loser(),
        "expectancy": Trade.objects.get_expectancy(),
        "winning_days_count": Trade.objects.get_winning_days_count(),
        "losing_days_count": Trade.objects.get_losing_days_count(),
        "winning_day_percent": Trade.objects.get_winning_days_percent(),
    }

    return render(request, "index.html", context)
