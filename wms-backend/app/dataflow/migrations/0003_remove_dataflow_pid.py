# Generated by Django 3.2 on 2021-05-11 06:32

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('dataflow', '0002_auto_20210511_0831'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='dataflow',
            name='pid',
        ),
    ]
