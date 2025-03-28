# Generated by Django 5.1.7 on 2025-03-24 15:29

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0058_alter_flexformfield_ordering_alter_formset_ordering"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="validator",
            options={"verbose_name": "Validator", "verbose_name_plural": "Validators"},
        ),
        migrations.AlterField(
            model_name="customfieldtype",
            name="name",
            field=models.CharField(
                max_length=100,
                unique=True,
                validators=[django.core.validators.RegexValidator("[A-Z][a-zA-Z0-9_]*")],
            ),
        ),
        migrations.AlterField(
            model_name="flexform",
            name="name",
            field=models.CharField(max_length=255, unique=True),
        ),
        migrations.AlterField(
            model_name="flexformfield",
            name="name",
            field=models.CharField(
                blank=True,
                max_length=100,
                validators=[django.core.validators.RegexValidator("^[a-z_0-9]*$")],
            ),
        ),
        migrations.AlterField(
            model_name="optionset",
            name="name",
            field=models.CharField(
                max_length=100,
                unique=True,
                validators=[django.core.validators.RegexValidator("[a-z0-9-_]")],
            ),
        ),
        migrations.AlterField(
            model_name="organization",
            name="name",
            field=models.CharField(max_length=100, unique=True),
        ),
        migrations.AlterField(
            model_name="project",
            name="name",
            field=models.CharField(max_length=100, unique=True),
        ),
        migrations.AlterField(
            model_name="validator",
            name="label",
            field=models.CharField(max_length=255),
        ),
        migrations.AlterField(
            model_name="validator",
            name="name",
            field=models.CharField(
                blank=True,
                max_length=255,
                null=True,
                unique=True,
                verbose_name="Function Name",
            ),
        ),
    ]
