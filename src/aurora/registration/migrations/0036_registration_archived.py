# Generated by Django 3.2.15 on 2022-08-18 06:47

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("registration", "0035_registration_unique_field_path"),
    ]

    operations = [
        migrations.AddField(
            model_name="registration",
            name="archived",
            field=models.BooleanField(
                default=False,
                help_text="Archived/Terminated registration cannot be activated/reopened",
            ),
        ),
    ]
