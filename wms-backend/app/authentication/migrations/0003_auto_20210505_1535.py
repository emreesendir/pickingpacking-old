# Generated by Django 3.2 on 2021-05-05 13:35

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('authentication', '0002_rename_permissons_permisson'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='permisson',
            name='user',
        ),
        migrations.CreateModel(
            name='UserPermisson',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('permissons', models.ManyToManyField(to='authentication.Permisson')),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
