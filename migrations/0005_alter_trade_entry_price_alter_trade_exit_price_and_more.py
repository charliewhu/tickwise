# Generated by Django 5.1.1 on 2024-10-06 13:47

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("main", "0004_trade_entered_at_trade_exited_at"),
    ]

    operations = [
        migrations.AlterField(
            model_name="trade",
            name="entry_price",
            field=models.DecimalField(decimal_places=5, max_digits=12),
        ),
        migrations.AlterField(
            model_name="trade",
            name="exit_price",
            field=models.DecimalField(decimal_places=5, max_digits=12),
        ),
        migrations.AlterField(
            model_name="trade",
            name="stop_price",
            field=models.DecimalField(decimal_places=5, max_digits=12),
        ),
        migrations.AlterField(
            model_name="trade",
            name="target_price",
            field=models.DecimalField(decimal_places=5, max_digits=12),
        ),
    ]
