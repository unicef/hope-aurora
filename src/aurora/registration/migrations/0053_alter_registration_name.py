# Generated by Django 4.2.10 on 2024-05-02 23:32

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("registration", "0052_alter_registration_slug"),
    ]

    operations = [
        migrations.AlterField(
            model_name="registration",
            name="name",
            field=models.CharField(db_collation="_", max_length=255),
        ),
    ]
