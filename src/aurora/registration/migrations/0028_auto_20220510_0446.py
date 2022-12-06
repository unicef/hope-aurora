# Generated by Django 3.2.13 on 2022-05-10 04:46

import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("registration", "0027_alter_registration_slug"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="registration",
            options={"get_latest_by": "start", "permissions": (("can_manage", "Can Manage"),)},
        ),
        migrations.AlterField(
            model_name="record",
            name="timestamp",
            field=models.DateTimeField(db_index=True, default=django.utils.timezone.now),
        ),
    ]