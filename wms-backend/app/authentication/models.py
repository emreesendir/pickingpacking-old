from django.conf import settings
from django.db.models.deletion import DO_NOTHING
from django.db.models.fields import CharField
from django.db.models.signals import post_save
from django.dispatch import receiver
from rest_framework.authtoken.models import Token
from django.contrib.auth.models import User
from django.db import models

@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_auth_token(sender, instance=None, created=False, **kwargs):
    if created:
        Token.objects.create(user=instance)

class Permission(models.Model):
    permission = models.CharField(max_length=100)

    def __str__(self):
        return self.permission

class UserPermission(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    permissions = models.ManyToManyField(Permission)

    def __str__(self):
        return self.user.username