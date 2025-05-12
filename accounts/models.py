from django.contrib.auth.models import User
from django.db import models

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    line_user_id = models.CharField(max_length=64, blank=True, null=True, unique=True)
    link_code = models.CharField(max_length=6, blank=True, null=True)

    def __str__(self):
        return self.user.username
