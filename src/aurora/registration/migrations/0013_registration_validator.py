# Generated by Django 3.2.12 on 2022-03-22 06:25

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0029_alter_validator_target"),
        ("registration", "0012_alter_registration_locale"),
    ]

    operations = [
        migrations.AddField(
            model_name="registration",
            name="validator",
            field=models.ForeignKey(
                blank=True,
                limit_choices_to={"target": "module"},
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                to="core.validator",
            ),
        ),
    ]
