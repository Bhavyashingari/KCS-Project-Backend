from rest_framework import serializers
from .models import Room, Message, User
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

User = get_user_model()

class RoomSerializer(serializers.ModelSerializer):
    admin_user = serializers.CharField()  # Accept username as a string
    room_id = serializers.ReadOnlyField()
    print("inside room serial")
    class Meta:
        model = Room
        fields = ['room_id', 'room_name', 'admin_user', 'is_broadcast', 'created_at', 'updated_at']

    def validate_admin_user(self, value):
        # Fetch the user by the username
        try:
            user = User.objects.get(username=value)  # Fetch user by username
            print(user)
        except User.DoesNotExist:
            raise serializers.ValidationError("User with the given username does not exist.")
        
        return user  # Return the user instance instead of the username

    def create(self, validated_data):
        # Extract admin_user from validated_data
        admin_user = validated_data.pop('admin_user')

        # Generate a unique room ID
        validated_data['room_id'] = f"ROOM_{Room.objects.count() + 1}"
        validated_data['admin_user'] = admin_user

        # Create the room
        room = super().create(validated_data)

        # Automatically add admin_user as a member of the room
        room.users.add(admin_user)  # Assuming 'users' is a ManyToManyField on the Room model
        room.save()

        return room

class RoomNameSerializer(serializers.ModelSerializer):
    room_name = serializers.CharField()

    class Meta:
        model = Room
        fields = ['room_name', 'room_id', 'created_at', "admin_user"]

class AddUserToRoomSerializer(serializers.Serializer):
    room_id = serializers.CharField()
    user_ids = serializers.ListField(child=serializers.IntegerField())

    def validate(self, data):
        # Check if the room exists
        try:
            data['room'] = Room.objects.get(room_id=data['room_id'])
        except Room.DoesNotExist:
            raise serializers.ValidationError("Room not found.")

        # Check if all users exist
        users = User.objects.filter(id__in=data['user_ids'])
        if not users or len(users) != len(data['user_ids']):
            raise serializers.ValidationError("One or more users not found.")
        data['users'] = users

        return data

    def save(self, **kwargs):
        room = self.validated_data['room']
        users = self.validated_data['users']

        # Add the users to the room
        room.users.add(*users)
        return room


class MessageSerializer(serializers.ModelSerializer):
    first_name = serializers.CharField(source='user.first_name', read_only=True)
    last_name = serializers.CharField(source='user.last_name', read_only=True)
    class Meta:
        model = Message
        fields = ['message_id', 'content', 'timestamp', 'room','first_name', 'last_name']  # Include fields as needed


class AddMessageSerializer(serializers.ModelSerializer):
    room_id = serializers.CharField(write_only=True)
    user_id = serializers.IntegerField(write_only=True)  # Use IntegerField for the user ID

    class Meta:
        model = Message
        fields = ['room_id', 'user_id', 'content']

    def create(self, validated_data):
        room_id = validated_data.pop('room_id')
        user_id = validated_data.pop('user_id')

        # Fetch room based on room_id
        from .models import Room  # Avoiding circular imports
        try:
            room = Room.objects.get(room_id=room_id)
        except Room.DoesNotExist:
            raise serializers.ValidationError({"room_id": "Room not found."})

        # Fetch user based on their ID
        try:
            user = User.objects.get(id=user_id)  # Use `id` instead of `user_id`
        except User.DoesNotExist:
            raise serializers.ValidationError({"user_id": "User not found."})

        # Create and return the message
        message = Message.objects.create(room=room, user=user, **validated_data)
        return message

class SignupSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    confirmPassword = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields = ['id', 'first_name', 'last_name', 'email', 'password', 'confirmPassword', 'created_date', 'updated_date']
        read_only_fields = ['created_date', 'updated_date']

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

        temp_username = f"TEMP_USER_{int(User.objects.latest('id').id) + 1}" if User.objects.exists() else "TEMP_USER_1"

        # Create the user instance without setting the username
        user = User.objects.create_user(
            username=temp_username,
            email=validated_data['email'],
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name'],
            password=validated_data['password']  # Password will be hashed automatically
        )

        # Set the username dynamically based on the user ID
        user.username = f"KCS_USER_{user.id}"
        user.save()

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
