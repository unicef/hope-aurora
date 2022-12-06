# Generated by Django 3.2.13 on 2022-04-17 09:19

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0038_auto_20220417_0554"),
    ]

    operations = [
        migrations.AlterField(
            model_name="validator",
            name="active",
            field=models.BooleanField(blank=True, default=False, help_text="Enable/Disable validator."),
        ),
        migrations.AlterField(
            model_name="validator",
            name="draft",
            field=models.BooleanField(
                blank=True,
                default=False,
                help_text="Testing purposes: draft validator are enabled only for staff users.",
            ),
        ),
        migrations.AlterField(
            model_name="validator",
            name="message",
            field=models.CharField(help_text="Default error message if validator return 'false'.", max_length=255),
        ),
        migrations.AlterField(
            model_name="validator",
            name="trace",
            field=models.BooleanField(
                default=False, help_text="Debug/Testing purposes: trace validator invocation on Sentry."
            ),
        ),
    ]