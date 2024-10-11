from decimal import Decimal, InvalidOperation
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


class BaseModel(models.Model):
    class Meta:  # type: ignore
        abstract = True

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class Account(BaseModel):
    # TODO: broker account info fields

    if t.TYPE_CHECKING:
        transactions = RelatedManager["AccountTransaction"]()
        trades = RelatedManager["Trade"]()

    # summary statistics
    def get_current_balance(self):
        """
        Sum of all deposits, withdrawals and trade PnL
        """
        total_transactions = self.transactions.aggregate(
            total=models.Sum("amount", default=0)
        )["total"]

        total_trade_pnl = self.trades.aggregate(
            total=models.Sum("profit_loss", default=0)
        )["total"]

        total_trade_fees = self.trades.aggregate(total=models.Sum("fees", default=0))[
            "total"
        ]

        return round(total_transactions + total_trade_pnl - total_trade_fees, 2)

    # list objects


@admin.register(Account)
class AccountAdmin(admin.ModelAdmin):
    pass


class AccountTransaction(BaseModel):
    account = models.ForeignKey(
        Account,
        on_delete=models.CASCADE,
        related_name="transactions",
    )
    date = models.DateField()
    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        help_text="Use positive values for Deposit, negative for Withdrawals",
    )

    def __str__(self) -> str:
        return f"{self.created_at.strftime('%H:%M-%d/%m/%Y')}: {self.transaction_type} {abs(self.amount)}"

    @property
    def transaction_type(self):
        if self.amount > 0:
            return "Deposit"
        else:
            return "Withdrawal"


@admin.register(AccountTransaction)
class AccountTransactionAdmin(admin.ModelAdmin):
    pass


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


class EntryTrigger(BaseModel):
    name = models.CharField(max_length=30)
    description = models.TextField(max_length=200, null=True, blank=True)

    if t.TYPE_CHECKING:
        trades = RelatedManager["Trade"]()

    def __str__(self) -> str:
        return self.name


@admin.register(EntryTrigger)
class EntryTriggerAdmin(admin.ModelAdmin):
    pass


class ExitTrigger(BaseModel):
    name = models.CharField(max_length=30)
    description = models.TextField(max_length=200, null=True, blank=True)

    if t.TYPE_CHECKING:
        trades = RelatedManager["Trade"]()

    def __str__(self) -> str:
        return self.name


@admin.register(ExitTrigger)
class ExitTriggerAdmin(admin.ModelAdmin):
    pass


class ManagementStrategy(BaseModel):
    name = models.CharField(max_length=30)
    description = models.TextField(max_length=200, null=True, blank=True)

    if t.TYPE_CHECKING:
        trades = RelatedManager["Trade"]()

    def __str__(self) -> str:
        return self.name


@admin.register(ManagementStrategy)
class ManagementStrategyAdmin(admin.ModelAdmin):
    pass


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
            return round(Decimal(self.get_win_count() / self.count()), 3)
        except ZeroDivisionError:
            return 0

    def get_average_planned_r(self):
        try:
            return round(
                self.aggregate(models.Sum("planned_r", default=0))["planned_r__sum"]
                / self.count(),
                2,
            )

        except (ZeroDivisionError, InvalidOperation):
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
            return Decimal(
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
        return self.get_total_return() / self.get_total_trading_days_count()

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
        transactions = Trade.objects.order_by("exited_at").values_list(
            "actual_r", flat=True
        )

        max_streak = 0
        current_streak = 0

        for actual_r in transactions:
            current_streak = current_streak + 1 if actual_r > 0 else 0
            max_streak = max(max_streak, current_streak)

        return max_streak

    def get_max_consecutive_losers(self):
        transactions = Trade.objects.order_by("exited_at").values_list(
            "actual_r", flat=True
        )

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


class Trade(BaseModel):
    GRADE_CHOICES = [
        ("a", "A"),
        ("b", "B"),
        ("c", "C"),
    ]

    account = models.ForeignKey(
        Account,
        on_delete=models.CASCADE,
        related_name="trades",
    )

    ticker = models.ForeignKey(
        Ticker,
        on_delete=models.SET_NULL,
        null=True,
        related_name="trades",
    )
    direction = models.CharField(
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
    hit_original_target = models.BooleanField(blank=True, null=True)
    profit_loss = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="The Profit/Loss on the trade in £. Do not include fees",
    )

    fees = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="The fees paid on the trade. Use negative numbers for costs.",
    )

    entry_trigger = models.ForeignKey(
        EntryTrigger,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="trades",
    )

    exit_trigger = models.ForeignKey(
        ExitTrigger,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="trades",
    )

    management_strategy = models.ForeignKey(
        ManagementStrategy,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="trades",
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

    # generated fields
    planned_r = models.GeneratedField(  # type: ignore
        expression=models.Case(
            models.When(
                models.Q(direction__exact="LONG"),
                then=(models.F("target_price") - models.F("entry_price"))
                / (models.F("entry_price") - models.F("stop_price")),
            ),
            models.When(
                models.Q(direction__exact="SHORT"),
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
                models.Q(direction__exact="LONG"),
                then=(models.F("exit_price") - models.F("entry_price"))
                / (models.F("entry_price") - models.F("stop_price")),
            ),
            models.When(
                models.Q(direction__exact="SHORT"),
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
                models.Q(direction__exact="LONG"),
                then=models.Q(exit_price__gt=models.F("entry_price")),
            ),
            models.When(
                models.Q(direction__exact="SHORT"),
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
                    models.Q(direction__iexact="SHORT")
                    | models.Q(entry_price__gt=models.F("stop_price"))
                ),
                name="check_valid_long_entry_and_stop_price",
                violation_error_message="Entry price must be greater than stop loss price",
            ),
            models.CheckConstraint(
                check=(
                    models.Q(direction__iexact="SHORT")
                    | models.Q(target_price__gt=models.F("entry_price"))
                ),
                name="check_valid_long_entry_and_target_price",
                violation_error_message="Target price must be greater than entry price",
            ),
            models.CheckConstraint(
                check=(
                    models.Q(direction__iexact="LONG")
                    | models.Q(entry_price__lt=models.F("stop_price"))
                ),
                name="check_valid_short_entry_and_stop_price",
                violation_error_message="Entry price must be less than stop loss price",
            ),
            models.CheckConstraint(
                check=(
                    models.Q(direction__iexact="LONG")
                    | models.Q(target_price__lt=models.F("entry_price"))
                ),
                name="check_valid_short_entry_and_target_price",
                violation_error_message="Target price must be less than entry price",
            ),
            models.CheckConstraint(
                check=(
                    # Ensure both fields are either null or non-null
                    models.Q(
                        exit_price__isnull=True, profit_loss__isnull=True
                    )  # both are null
                    | models.Q(
                        exit_price__isnull=False, profit_loss__isnull=False
                    )  # both are non-null
                ),
                name="check_both_or_neither_exit_and_pnl_null",
                violation_error_message="You must enter both Exit Price and Profit/Loss Amount",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.direction} {self.ticker} at {self.entered_at.strftime('%H:%M-%d/%m/%Y')}"

    @property
    def is_long(self):
        return self.direction == "LONG"


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
        "total_return": Trade.objects.get_total_return(),
        "win_count": Trade.objects.get_win_count(),
        "loss_count": Trade.objects.get_loss_count(),
        "strike_rate": round(Trade.objects.get_strike_rate() * 100, 1),
        "average_trade": Trade.objects.get_average_trade(),
        "average_winner": Trade.objects.get_average_winner(),
        "average_loser": Trade.objects.get_average_loser(),
        "average_planned_r": Trade.objects.get_average_planned_r(),
        "expectancy": Trade.objects.get_expectancy(),
        "average_trading_day_r": Trade.objects.get_average_trading_day_r(),
        "profit_factor": Trade.objects.get_profit_factor(),
        "winning_days_count": Trade.objects.get_winning_days_count(),
        "losing_days_count": Trade.objects.get_losing_days_count(),
        "winning_day_percent": Trade.objects.get_winning_days_percent(),
        "max_consecutive_winners": Trade.objects.get_max_consecutive_winners(),
        "max_consecutive_losers": Trade.objects.get_max_consecutive_losers(),
        "current_balance": Account.objects.get(pk=1).get_current_balance(),
        "trades": Trade.objects.all(),
    }

    return render(request, "index.html", context)
