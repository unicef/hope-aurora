# Generated by Django 3.2.16 on 2023-02-08 11:33

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("registration", "0044_auto_20230126_1226"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="registration",
            options={
                "get_latest_by": "start",
                "ordering": ("name", "title"),
                "permissions": (
                    ("manage", "Can manage Registration"),
                    ("register", "Can use Registration"),
                    ("create_translation", "Can Create Translation"),
                ),
            },
        ),
        migrations.RemoveField(
            model_name="registration",
            name="organization",
        ),
    ]
