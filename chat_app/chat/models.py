from django.db import models
from django.contrib.auth.models import AbstractUser, UserManager

class Room(models.Model):
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name

class Message(models.Model):
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name='messages')
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Message in {self.room.name} at {self.timestamp}'

class UserManager(UserManager):
    def create_superuser(self, email, first_name, last_name, password=None, **extra_fields):
        """
        Create and return a superuser with an email and password.
        """
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, first_name=first_name, last_name=last_name, **extra_fields)
        user.set_password(password)
        user.is_staff = True
        user.is_superuser = True
        user.save(using=self._db)
        return user

class User(AbstractUser):
    email = models.EmailField(unique=True)
    
    REQUIRED_FIELDS = ['first_name', 'last_name']
    USERNAME_FIELD = 'email' 
    objects = UserManager()

    def __str__(self):
        return self.email