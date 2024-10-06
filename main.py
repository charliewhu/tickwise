from django import forms
from django.db import models
from django.http import HttpRequest
from django.shortcuts import render

from nanodjango import Django

app = Django()


@app.admin()
class Trade(models.Model):
    GRADE_CHOICES = [
        ("a", "A"),
        ("b", "B"),
        ("c", "C"),
    ]

    long_short_flag = models.TextField(choices=[("LONG", "Long"), ("SHORT", "Short")])
    entry_price = models.FloatField()
    exit_price = models.FloatField()

    entry_grade = models.TextField(
        max_length=1,
        choices=GRADE_CHOICES,
        null=True,
        blank=True,
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class TradeForm(forms.ModelForm):
    class Meta:  # type: ignore
        model = Trade
        fields = [
            "long_short_flag",
            "entry_price",
            "exit_price",
        ]


@app.route("/")
def index(request: HttpRequest):
    if request.method == "POST":
        form = TradeForm(request.POST)
        if form.is_valid():
            form.save()
            return "Author added"

    return render(request, "form.html", {"form": TradeForm()})
