from rest_framework import serializers
from .models import Room, Message, User
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

User=get_user_model()

class RoomSerializer(serializers.ModelSerializer):
    class Meta:
        model = Room
        fields = '__all__'


class MessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Message
        fields = '__all__'

class SignupSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    confirmPassword = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields = ['id', 'first_name', 'last_name', 'email', 'password', 'confirmPassword']
    
    def validate_email(self, value):
        """
        Custom validation to check if the email already exists.
        """
        if User.objects.filter(email__iexact=value).exists():
            raise ValidationError("A user with this email already exists.")
        return value

    def validate(self, data):
        """
        Custom validation to check if password and confirmPassword match.
        """
        if data['password'] != data['confirmPassword']:
            raise ValidationError("Passwords do not match")
        return data

    def create(self, validated_data):
        # Remove confirmPassword from validated_data as it's not required for creating the user
        validated_data.pop('confirmPassword')

        # Create user
        user = User.objects.create_user(
            username=validated_data['email'],  # Assuming email is used as username
            email=validated_data['email'],
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name'],
            password=validated_data['password']  # Password will be hashed automatically
        )
        return user

    
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = get_user_model()
        fields = ['id', 'first_name', 'last_name', 'email']


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)

        # Add custom claims to the token
        token['email'] = user.email
        token['first_name'] = user.first_name
        token['last_name'] = user.last_name

        return token