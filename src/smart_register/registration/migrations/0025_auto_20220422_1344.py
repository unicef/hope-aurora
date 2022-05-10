# Generated by Django 3.2.13 on 2022-04-22 13:44

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ("registration", "0024_auto_20220412_1408"),
    ]

    operations = [
        migrations.AlterField(
            model_name="registration",
            name="slug",
            field=models.SlugField(blank=True, max_length=500, null=True, unique=False),
        ),
        migrations.AlterField(
            model_name="registration",
            name="start",
            field=models.DateField(default=django.utils.timezone.now),
        ),
    ]
