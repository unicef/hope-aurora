# Generated by Django 3.2.12 on 2022-04-02 11:50

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0035_auto_20220402_1124"),
    ]

    operations = [
        migrations.AddField(
            model_name="optionset",
            name="last_update_date",
            field=models.DateTimeField(auto_now=True),
        ),
    ]
