# Generated by Django 3.2.23 on 2023-12-14 14:47

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('registration', '0051_auto_20231123_0605'),
    ]

    operations = [
        migrations.AlterField(
            model_name='registration',
            name='slug',
            field=models.SlugField(blank=True, max_length=500, null=True, unique=True),
        ),
    ]