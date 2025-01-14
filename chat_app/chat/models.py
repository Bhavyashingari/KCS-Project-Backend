from django.db import models
from django.contrib.auth.models import AbstractUser, UserManager, User
from django.conf import settings  # Import settings to refer to AUTH_USER_MODEL

class Room(models.Model):
    room_id = models.CharField(max_length=50, unique=True)
    room_name = models.CharField(max_length=255, unique=True)
    admin_user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="admin_rooms")
    is_broadcast = models.BooleanField(default=False)
    users = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name="joined_rooms")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.room_name

class Message(models.Model):
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name='messages')
    message_id = models.CharField(max_length=75, unique=True, blank=True, db_index=True)
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Message in {self.room.name} at {self.timestamp}'

    def save(self, *args, **kwargs):
        # Generate message_id if not already set
        if not self.message_id:
            last_message = Message.objects.order_by('-id').first()
            if last_message:
                last_id = int(last_message.message_id.split('_')[-1])
                self.message_id = f'KCS_MESSAGE_{last_id + 1}'
            else:
                self.message_id = 'KCS_MESSAGE_1'
        super().save(*args, **kwargs)

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
    created_date = models.DateTimeField(auto_now_add=True)  # Automatically set when a user is created
    updated_date = models.DateTimeField(auto_now=True)  # Automatically updated when a user is modified

    REQUIRED_FIELDS = ['first_name', 'last_name']
    USERNAME_FIELD = 'email' 
    objects = UserManager()

    def __str__(self):
        return self.email