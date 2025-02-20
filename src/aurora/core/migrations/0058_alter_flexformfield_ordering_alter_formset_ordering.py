# Generated by Django 5.1.5 on 2025-01-22 00:10

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0057_alter_customfieldtype_name_alter_flexform_name_and_more"),
    ]

    operations = [
        migrations.AlterField(
            model_name="flexformfield",
            name="ordering",
            field=models.PositiveIntegerField(db_index=True, default=0, verbose_name="ordering"),
        ),
        migrations.AlterField(
            model_name="formset",
            name="ordering",
            field=models.PositiveIntegerField(db_index=True, default=0, verbose_name="ordering"),
        ),
    ]
