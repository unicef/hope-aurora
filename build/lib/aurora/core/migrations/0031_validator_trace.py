# Generated by Django 3.2.12 on 2022-03-22 21:37

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0030_alter_flexformfield_name"),
    ]

    operations = [
        migrations.AddField(
            model_name="validator",
            name="trace",
            field=models.BooleanField(default=False),
        ),
    ]
