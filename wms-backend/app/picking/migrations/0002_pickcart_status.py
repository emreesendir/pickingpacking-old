# Generated by Django 3.2 on 2021-06-01 07:29

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('picking', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='pickcart',
            name='status',
            field=models.CharField(default='AVAILABLE', max_length=25),
        ),
    ]
