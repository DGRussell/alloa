# Generated by Django 2.2.24 on 2022-02-15 11:32

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('alloa_matching', '0004_auto_20211216_1302'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='instance',
            name='level',
        ),
        migrations.AddField(
            model_name='instance',
            name='max_pref_len',
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AddField(
            model_name='instance',
            name='min_pref_len',
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AlterField(
            model_name='academic',
            name='lower_cap',
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AlterField(
            model_name='academic',
            name='upper_cap',
            field=models.PositiveIntegerField(default=1),
        ),
        migrations.AlterField(
            model_name='advisorlevel',
            name='level',
            field=models.PositiveIntegerField(choices=[(1, 'Expert Knowledge'), (2, 'High Knowledge'), (3, 'Good Knowledge')], default=1),
        ),
        migrations.AlterField(
            model_name='choice',
            name='rank',
            field=models.PositiveIntegerField(default=1),
        ),
        migrations.AlterField(
            model_name='instance',
            name='stage',
            field=models.CharField(choices=[('N', 'New'), ('P', 'Project Proposal'), ('L', 'Lecturer Ranking Levels'), ('S', 'Student Preference Collection'), ('C', 'Closed'), ('R', 'Results Available')], default='N', max_length=1),
        ),
        migrations.AlterField(
            model_name='project',
            name='lower_cap',
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AlterField(
            model_name='project',
            name='upper_cap',
            field=models.PositiveIntegerField(default=1),
        ),
        migrations.AlterField(
            model_name='student',
            name='lower_cap',
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AlterField(
            model_name='student',
            name='upper_cap',
            field=models.PositiveIntegerField(default=1),
        ),
        migrations.AlterField(
            model_name='userprofile',
            name='user_type',
            field=models.CharField(choices=[('ST', 'Student'), ('AC', 'Academic'), ('AD', 'Admin')], default='ST', max_length=2),
        ),
    ]
