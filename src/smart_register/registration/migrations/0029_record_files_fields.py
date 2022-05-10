# Generated by Django 3.2.13 on 2022-04-27 10:39

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("registration", "0028_auto_20220510_0446"),
    ]

    operations = [
        migrations.AddField(
            model_name="record",
            name="fields",
            field=models.JSONField(blank=True, default=dict, null=True),
        ),
        migrations.AddField(
            model_name="record",
            name="files",
            field=models.BinaryField(blank=True, null=True),
        ),
    ]
