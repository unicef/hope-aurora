# Generated by Django 4.2.10 on 2024-05-03 06:32

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0056_case_insensitive_collation"),
    ]

    operations = [
        migrations.AlterField(
            model_name="customfieldtype",
            name="name",
            field=models.CharField(
                db_collation="_",
                max_length=100,
                unique=True,
                validators=[django.core.validators.RegexValidator("[A-Z][a-zA-Z0-9_]*")],
            ),
        ),
        migrations.AlterField(
            model_name="flexform",
            name="name",
            field=models.CharField(db_collation="_", max_length=255, unique=True),
        ),
        migrations.AlterField(
            model_name="flexformfield",
            name="name",
            field=models.CharField(
                blank=True,
                db_collation="_",
                max_length=100,
                validators=[django.core.validators.RegexValidator("^[a-z_0-9]*$")],
            ),
        ),
        migrations.AlterField(
            model_name="formset",
            name="name",
            field=models.CharField(max_length=255),
        ),
        migrations.AlterField(
            model_name="optionset",
            name="name",
            field=models.CharField(
                db_collation="_",
                max_length=100,
                unique=True,
                validators=[django.core.validators.RegexValidator("[a-z0-9-_]")],
            ),
        ),
        migrations.AlterField(
            model_name="organization",
            name="name",
            field=models.CharField(db_collation="_", max_length=100, unique=True),
        ),
        migrations.AlterField(
            model_name="project",
            name="name",
            field=models.CharField(db_collation="_", max_length=100, unique=True),
        ),
        migrations.AlterField(
            model_name="validator",
            name="label",
            field=models.CharField(db_collation="_", max_length=255),
        ),
        migrations.AlterField(
            model_name="validator",
            name="name",
            field=models.CharField(
                blank=True,
                db_collation="_",
                max_length=255,
                null=True,
                unique=True,
                verbose_name="Function Name",
            ),
        ),
    ]
