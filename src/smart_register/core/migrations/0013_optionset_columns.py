# Generated by Django 3.2.12 on 2022-03-13 06:58

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0012_auto_20220311_0514"),
    ]

    operations = [
        migrations.AddField(
            model_name="optionset",
            name="columns",
            field=models.CharField(blank=True, default="label", max_length=10),
        ),
    ]
