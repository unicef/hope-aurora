# Generated by Django 3.2.12 on 2022-03-08 20:49

import django.contrib.postgres.fields.citext
import django.core.validators
from django.db import migrations
import smart_register.core.forms
import strategy_field.fields


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0006_flexform_base_type"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="customfieldtype",
            name="choices",
        ),
        migrations.RemoveField(
            model_name="customfieldtype",
            name="required",
        ),
        migrations.AlterField(
            model_name="customfieldtype",
            name="name",
            field=django.contrib.postgres.fields.citext.CICharField(
                max_length=100, unique=True, validators=[django.core.validators.RegexValidator("[A-Z][a-zA-Z0-9_]*")]
            ),
        ),
        migrations.AlterField(
            model_name="flexform",
            name="base_type",
            field=strategy_field.fields.StrategyClassField(default=smart_register.core.forms.FlexFormBaseForm),
        ),
    ]
