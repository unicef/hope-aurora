# Generated by Django 3.2.12 on 2022-03-22 11:15

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("registration", "0013_registration_validator"),
    ]

    operations = [
        migrations.AddField(
            model_name="registration",
            name="footer",
            field=models.TextField(blank=True, null=True),
        ),
    ]
