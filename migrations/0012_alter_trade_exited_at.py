# Generated by Django 5.1.1 on 2024-10-06 15:01

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("main", "0011_alter_trade_exit_price"),
    ]

    operations = [
        migrations.AlterField(
            model_name="trade",
            name="exited_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
