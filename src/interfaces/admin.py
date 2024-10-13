from django.contrib import admin

from src.data import models


@admin.register(models.Account)
class AccountAdmin(admin.ModelAdmin):
    pass


@admin.register(models.AccountTransaction)
class AccountTransactionAdmin(admin.ModelAdmin):
    pass


@admin.register(models.Ticker)
class TickerAdmin(admin.ModelAdmin):
    pass


@admin.register(models.Timeframe)
class TimeframeAdmin(admin.ModelAdmin):
    pass


@admin.register(models.EntryTrigger)
class EntryTriggerAdmin(admin.ModelAdmin):
    pass


@admin.register(models.ExitTrigger)
class ExitTriggerAdmin(admin.ModelAdmin):
    pass


@admin.register(models.ManagementStrategy)
class ManagementStrategyAdmin(admin.ModelAdmin):
    pass


@admin.register(models.ConfluenceOption)
class ConfluenceOptionAdmin(admin.ModelAdmin):
    model = models.ConfluenceOption


class ConfluenceOptionInlineAdmin(admin.StackedInline):
    model = models.ConfluenceOption


class ConfluenceAdmin(admin.ModelAdmin):
    inlines = [ConfluenceOptionInlineAdmin]


admin.site.register(models.Confluence, ConfluenceAdmin)


@admin.register(models.Trade)
class TradeAdmin(admin.ModelAdmin):
    readonly_fields = [
        "planned_r",
        "actual_r",
        "is_winner",
        "mae_percent",
    ]

    fieldsets = [
        (
            None,
            {
                "fields": [
                    "account",
                    "ticker",
                    "direction",
                ],
            },
        ),
        (
            "Entry Inputs",
            {
                "classes": ["collapse"],
                "fields": [
                    "entered_at",
                    "entry_price",
                    "stop_price",
                    "target_price",
                    "trigger_timeframe",
                    "entry_trigger",
                    "confluences",
                ],
            },
        ),
        (
            "Exit Inputs",
            {
                "classes": ["collapse"],
                "fields": [
                    "exited_at",
                    "exit_price",
                    "exit_trigger",
                    "profit_loss",
                    "fees",
                    "management_strategy",
                ],
            },
        ),
        (
            "Post Trade Inputs",
            {
                "classes": ["collapse"],
                "fields": [
                    "min_price_during_trade",
                    "max_price_during_trade",
                    "hit_original_target",
                    "entry_grade",
                    "exit_grade",
                ],
            },
        ),
        (
            "Trade Stats",
            {
                "classes": ["collapse"],
                "fields": [
                    "is_winner",
                    "planned_r",
                    "actual_r",
                    "mae_percent",
                ],
            },
        ),
    ]
