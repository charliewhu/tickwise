# Generated by Django 5.1.1 on 2024-10-06 14:12

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("main", "0006_trade_check_valid_long_prices"),
    ]

    operations = [
        migrations.AddConstraint(
            model_name="trade",
            constraint=models.CheckConstraint(
                condition=models.Q(
                    ("long_short_flag__iexact", "LONG"),
                    ("entry_price__gt", models.F("stop_price")),
                    ("target_price__gt", models.F("entry_price")),
                ),
                name="check_valid_entry_stop_price",
            ),
        ),
    ]
