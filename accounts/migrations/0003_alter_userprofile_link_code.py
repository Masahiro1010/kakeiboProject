# Generated by Django 5.1.7 on 2025-05-12 16:49

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0002_userprofile_link_code"),
    ]

    operations = [
        migrations.AlterField(
            model_name="userprofile",
            name="link_code",
            field=models.CharField(blank=True, max_length=6, null=True),
        ),
    ]
