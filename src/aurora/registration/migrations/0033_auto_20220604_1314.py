# Generated by Django 3.2.13 on 2022-06-04 13:14

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0046_alter_validator_target"),
        ("registration", "0032_auto_20220512_1744"),
    ]

    operations = [
        migrations.AddField(
            model_name="registration",
            name="unique_field_error",
            field=models.CharField(
                blank=True, help_text="Error message in case of duplicate 'unique_field'", max_length=255, null=True
            ),
        ),
    ]
