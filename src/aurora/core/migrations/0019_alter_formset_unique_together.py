# Generated by Django 3.2.12 on 2022-03-14 06:30

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0018_rename_required_formset_min_num"),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name="formset",
            unique_together={("parent", "flex_form", "name")},
        ),
    ]
