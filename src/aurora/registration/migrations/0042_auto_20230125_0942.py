# Generated by Django 3.2.16 on 2023-01-25 09:42

import aurora.registration.fields
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("registration", "0041_auto_20230123_1856"),
    ]

    operations = [
        migrations.AddField(
            model_name="record",
            name="is_offline",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="registration",
            name="is_pwa_enabled",
            field=models.BooleanField(default=False),
        ),
        migrations.AlterField(
            model_name="registration",
            name="locale",
            field=models.CharField(
                choices=[
                    ("en-us", "English | English"),
                    ("ar-ae", " | عربيArabic"),
                    ("cs-cz", "čeština | Czech"),
                    ("de-de", "Deutsch"),
                    ("es-es", "Español | Spanish"),
                    ("fr-fr", "Français | French"),
                    ("hu-hu", "Magyar | Hungarian"),
                    ("it-it", "Italiano"),
                    ("pl-pl", "Polskie | Polish"),
                    ("pt-pt", "Português"),
                    ("ro-ro", "Română"),
                    ("ru-ru", "Русский | Russian"),
                    ("si-si", "සිංහල | Sinhala"),
                    ("ta-ta", "தமிழ் | Tamil"),
                    ("uk-ua", "український | Ukrainian"),
                    ("hi-hi", "हिंदी"),
                ],
                default="en-us",
                max_length=10,
                verbose_name="Default locale",
            ),
        ),
        migrations.AlterField(
            model_name="registration",
            name="locales",
            field=aurora.registration.fields.ChoiceArrayField(
                base_field=models.CharField(
                    choices=[
                        ("en-us", "English | English"),
                        ("ar-ae", " | عربيArabic"),
                        ("cs-cz", "čeština | Czech"),
                        ("de-de", "Deutsch"),
                        ("es-es", "Español | Spanish"),
                        ("fr-fr", "Français | French"),
                        ("hu-hu", "Magyar | Hungarian"),
                        ("it-it", "Italiano"),
                        ("pl-pl", "Polskie | Polish"),
                        ("pt-pt", "Português"),
                        ("ro-ro", "Română"),
                        ("ru-ru", "Русский | Russian"),
                        ("si-si", "සිංහල | Sinhala"),
                        ("ta-ta", "தமிழ் | Tamil"),
                        ("uk-ua", "український | Ukrainian"),
                        ("hi-hi", "हिंदी"),
                    ],
                    max_length=10,
                ),
                blank=True,
                null=True,
                size=None,
            ),
        ),
    ]