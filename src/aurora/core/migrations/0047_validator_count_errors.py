# Generated by Django 3.2.12 on 2022-06-16 04:11

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0046_alter_validator_target"),
    ]

    operations = [
        migrations.AddField(
            model_name="validator",
            name="count_errors",
            field=models.BooleanField(default=False, help_text="Count failures"),
        ),
    ]
