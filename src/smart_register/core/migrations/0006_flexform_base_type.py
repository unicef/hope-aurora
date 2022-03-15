# Generated by Django 3.2.12 on 2022-03-08 11:24

from django.db import migrations
import django.forms.forms
import strategy_field.fields


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0005_remove_customfieldtype_clean"),
    ]

    operations = [
        migrations.AddField(
            model_name="flexform",
            name="base_type",
            field=strategy_field.fields.StrategyClassField(default=django.forms.forms.Form),
        ),
    ]
