# Generated by Django 3.2.12 on 2022-03-10 10:33

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0008_auto_20220310_0517"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="formset",
            options={
                "ordering": ["ordering"],
                "verbose_name": "FormSet",
                "verbose_name_plural": "FormSets",
            },
        ),
        migrations.AddField(
            model_name="formset",
            name="ordering",
            field=models.PositiveIntegerField(default=0, verbose_name="ordering"),
        ),
        migrations.AlterField(
            model_name="flexformfield",
            name="label",
            field=models.CharField(max_length=2000),
        ),
    ]
