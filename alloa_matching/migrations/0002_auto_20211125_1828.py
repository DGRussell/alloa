# Generated by Django 2.2.24 on 2021-11-25 18:28

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('alloa_matching', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='instance',
            name='available',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='instance',
            name='closed',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='instance',
            name='matching_computed',
            field=models.BooleanField(default=False),
        ),
    ]
