# Generated by Django 3.2.12 on 2022-03-19 18:21

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("registration", "0008_registration_slug"),
    ]

    operations = [
        migrations.AddField(
            model_name="registration",
            name="title",
            field=models.CharField(blank=True, max_length=500, null=True),
        ),
    ]
