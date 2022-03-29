# Generated by Django 3.2.12 on 2022-03-28 16:02

import django.contrib.postgres.fields
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("registration", "0015_alter_registration_locale"),
    ]

    operations = [
        migrations.AddField(
            model_name="registration",
            name="locales",
            field=django.contrib.postgres.fields.ArrayField(
                base_field=models.CharField(
                    blank=True,
                    choices=[
                        ("uk-ua", "український | Ukrainian"),
                        ("en-us", "English | English"),
                        ("pl-pl", "Polskie | Polish"),
                    ],
                    default="en-us",
                    max_length=10,
                ),
                blank=True,
                null=True,
                size=None,
            ),
        ),
        migrations.AlterField(
            model_name="registration",
            name="locale",
            field=models.CharField(
                choices=[
                    ("uk-ua", "український | Ukrainian"),
                    ("en-us", "English | English"),
                    ("pl-pl", "Polskie | Polish"),
                ],
                default="en-us",
                max_length=10,
            ),
        ),
        migrations.AlterUniqueTogether(
            name="registration",
            unique_together=set(),
        ),
    ]
