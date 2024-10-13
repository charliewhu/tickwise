import typing as t

from django.db import models

from .querysets import TradeQueryset


if t.TYPE_CHECKING:
    # This doesn't really exists on django so it always need to be imported this way
    from django.db.models.manager import RelatedManager


class BaseModel(models.Model):
    class Meta:  # type: ignore
        abstract = True

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class Account(BaseModel):
    name = models.CharField(max_length=20)

    if t.TYPE_CHECKING:
        transactions = RelatedManager["AccountTransaction"]()
        trades = RelatedManager["Trade"]()

    def __str__(self) -> str:
        return self.name

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


class Ticker(models.Model):
    name = models.CharField(max_length=10)

    if t.TYPE_CHECKING:
        trades = RelatedManager["Trade"]()

    def __str__(self) -> str:
        return self.name


class Timeframe(models.Model):
    name = models.CharField(max_length=10)

    if t.TYPE_CHECKING:
        trades = RelatedManager["Trade"]()

    def __str__(self) -> str:
        return self.name


class EntryTrigger(BaseModel):
    name = models.CharField(max_length=30)
    description = models.TextField(max_length=200, null=True, blank=True)

    if t.TYPE_CHECKING:
        trades = RelatedManager["Trade"]()

    def __str__(self) -> str:
        return self.name


class ExitTrigger(BaseModel):
    name = models.CharField(max_length=30)
    description = models.TextField(max_length=200, null=True, blank=True)

    if t.TYPE_CHECKING:
        trades = RelatedManager["Trade"]()

    def __str__(self) -> str:
        return self.name


class ManagementStrategy(BaseModel):
    class Meta:  # type: ignore
        verbose_name_plural = "Management Strategies"

    name = models.CharField(max_length=30)
    description = models.TextField(max_length=200, null=True, blank=True)

    if t.TYPE_CHECKING:
        trades = RelatedManager["Trade"]()

    def __str__(self) -> str:
        return self.name


class Confluence(BaseModel):
    name = models.CharField(max_length=30)
    description = models.TextField(max_length=200, null=True, blank=True)

    def __str__(self) -> str:
        return self.name


class ConfluenceOption(BaseModel):
    confluence = models.ForeignKey(
        Confluence,
        on_delete=models.CASCADE,
    )
    name = models.CharField(max_length=30)
    description = models.TextField(max_length=200, null=True, blank=True)

    if t.TYPE_CHECKING:
        trades = RelatedManager["Trade"]()

    def __str__(self) -> str:
        return f"{self.confluence} - {self.name}"


class Trade(BaseModel):
    GRADE_CHOICES = [
        ("a", "A"),
        ("b", "B"),
        ("c", "C"),
    ]

    # General trade data
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

    # Entry data
    entered_at = models.DateTimeField()
    entry_price = models.DecimalField(max_digits=12, decimal_places=5)
    stop_price = models.DecimalField(max_digits=12, decimal_places=5)
    target_price = models.DecimalField(max_digits=12, decimal_places=5)
    trigger_timeframe = models.ForeignKey(
        Timeframe,
        on_delete=models.SET_NULL,
        null=True,
        related_name="trades",
    )
    entry_trigger = models.ForeignKey(
        EntryTrigger,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="trades",
    )
    confluences = models.ManyToManyField(
        ConfluenceOption,
        related_name="trades",
    )

    # Exit data
    exited_at = models.DateTimeField(blank=True, null=True)
    exit_price = models.DecimalField(
        max_digits=12,
        decimal_places=5,
        blank=True,
        null=True,
    )
    exit_trigger = models.ForeignKey(
        ExitTrigger,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="trades",
    )
    profit_loss = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="The gross Profit/Loss on the trade in £. Do not include fees",
    )
    fees = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="The fees paid on the trade. Use negative numbers for costs.",
    )

    management_strategy = models.ForeignKey(
        ManagementStrategy,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="trades",
    )

    # Post trade reflection
    hit_original_target = models.BooleanField(blank=True, null=True)
    min_price_during_trade = models.DecimalField(
        max_digits=12,
        decimal_places=5,
        null=True,
        blank=True,
        help_text="The lowest price we reached during the trade length. Account for spread.",
    )
    max_price_during_trade = models.DecimalField(
        max_digits=12,
        decimal_places=5,
        null=True,
        blank=True,
        help_text="The highest price we reached during the trade length. Account for spread.",
    )
    entry_grade = models.CharField(
        max_length=1,
        choices=GRADE_CHOICES,
        null=True,
        blank=True,
        help_text="Now that the trade has been exited. Objectively rate the entry",
    )
    exit_grade = models.CharField(
        max_length=1,
        choices=GRADE_CHOICES,
        null=True,
        blank=True,
        help_text="Now that the trade has been exited. Objectively rate the exit",
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

    mae_percent = models.GeneratedField(  # type: ignore
        # Distance to stop reached divided by total stop size
        expression=models.Case(
            models.When(
                models.Q(direction__exact="LONG")
                & models.Q(min_price_during_trade__isnull=False),
                then=(
                    (models.F("entry_price") - models.F("min_price_during_trade"))
                    / (models.F("entry_price") - models.F("stop_price"))
                )
                * 100,
            ),
            models.When(
                models.Q(direction__exact="SHORT")
                & models.Q(max_price_during_trade__isnull=False),
                then=(
                    (models.F("max_price_during_trade") - models.F("entry_price"))
                    / (models.F("stop_price") - models.F("entry_price"))
                )
                * 100,
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
