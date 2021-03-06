# Generated by Django 3.2 on 2021-06-01 07:38

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('picking', '0002_pickcart_status'),
    ]

    operations = [
        migrations.CreateModel(
            name='PickCartSection',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('number', models.IntegerField()),
                ('barcode', models.CharField(max_length=25)),
                ('size', models.CharField(max_length=25)),
                ('pickcart', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='picking.pickcart')),
            ],
        ),
    ]
