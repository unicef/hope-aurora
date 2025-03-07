from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0034_auto_20220402_1124"),
    ]

    operations = [
        migrations.RunSQL(
            """UPDATE core_flexform SET version=1;
UPDATE core_optionset SET version=1;
UPDATE core_flexformfield SET version=1;
UPDATE core_formset SET version=1;""",
            "",
        )
    ]
