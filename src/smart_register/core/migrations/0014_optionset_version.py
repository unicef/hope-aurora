# Generated by Django 3.2.12 on 2022-03-13 07:05

import concurrency.fields
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0013_optionset_columns"),
    ]

    operations = [
        migrations.AddField(
            model_name="optionset",
            name="version",
            field=concurrency.fields.AutoIncVersionField(default=0, help_text="record revision number"),
        ),
    ]
