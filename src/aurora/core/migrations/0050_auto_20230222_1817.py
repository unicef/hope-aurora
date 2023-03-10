# Generated by Django 3.2.16 on 2023-02-22 18:17

import concurrency.fields
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0049_auto_20230214_1915"),
    ]

    operations = [
        migrations.AddField(
            model_name="customfieldtype",
            name="last_update_date",
            field=models.DateTimeField(auto_now=True),
        ),
        migrations.AddField(
            model_name="customfieldtype",
            name="version",
            field=concurrency.fields.AutoIncVersionField(default=0, help_text="record revision number"),
        ),
        migrations.AddField(
            model_name="organization",
            name="last_update_date",
            field=models.DateTimeField(auto_now=True),
        ),
        migrations.AddField(
            model_name="project",
            name="last_update_date",
            field=models.DateTimeField(auto_now=True),
        ),
    ]