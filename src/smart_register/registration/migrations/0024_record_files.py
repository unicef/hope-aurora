# Generated by Django 3.2.12 on 2022-04-14 08:42

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("registration", "0023_auto_20220414_0824"),
    ]

    operations = [
        migrations.AddField(
            model_name="record",
            name="files",
            field=models.BinaryField(blank=True, null=True),
        ),
    ]
