# Generated by Django 3.2.12 on 2022-03-21 05:07

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0026_formset_advanced"),
    ]

    operations = [
        migrations.AlterField(
            model_name="formset",
            name="advanced",
            field=models.JSONField(blank=True, default=dict),
        ),
    ]
