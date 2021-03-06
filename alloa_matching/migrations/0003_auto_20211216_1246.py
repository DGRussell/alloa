# Generated by Django 2.2.24 on 2021-12-16 12:46

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('alloa_matching', '0002_auto_20211125_1828'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='instance',
            name='available',
        ),
        migrations.RemoveField(
            model_name='instance',
            name='closed',
        ),
        migrations.RemoveField(
            model_name='instance',
            name='matching_computed',
        ),
        migrations.AddField(
            model_name='instance',
            name='stage',
            field=models.CharField(choices=[('N', 'New'), ('P', 'Project Proposal'), ('O', 'Open'), ('C', 'Closed'), ('R', 'Results Available')], default='N', max_length=1),
        ),
    ]
