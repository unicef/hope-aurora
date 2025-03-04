# Generated by Django 3.2.16 on 2023-01-26 12:26

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0048_auto_20230126_1226"),
        ("registration", "0043_remove_registration_unique_field"),
    ]

    operations = [
        migrations.AddField(
            model_name="registration",
            name="organization",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                to="core.organization",
            ),
        ),
        migrations.AddField(
            model_name="registration",
            name="project",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                to="core.project",
            ),
        ),
    ]
