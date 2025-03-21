# Generated by Django 3.2.13 on 2022-04-21 09:41

from django.db import migrations, models

import aurora.i18n.fields


class Migration(migrations.Migration):
    dependencies = [
        ("i18n", "0004_auto_20220412_1242"),
    ]

    operations = [
        migrations.AlterField(
            model_name="message",
            name="locale",
            field=aurora.i18n.fields.LanguageField(
                choices=[
                    ("uk-ua", "український | Ukrainian"),
                    ("en-us", "English | English"),
                    ("pl-pl", "Polskie | Polish"),
                ],
                db_index=True,
                default="en-us",
                max_length=10,
                null=True,
                verbose_name="Language",
            ),
        ),
        migrations.AlterField(
            model_name="message",
            name="msgid",
            field=models.TextField(db_index=True),
        ),
        migrations.AlterUniqueTogether(
            name="message",
            unique_together={("msgid", "locale")},
        ),
    ]
