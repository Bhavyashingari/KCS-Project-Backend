from sqlite3 import IntegrityError
from rest_framework.generics import CreateAPIView
from django.shortcuts import render
from rest_framework.generics import ListCreateAPIView, ListAPIView
from .models import Room, Message
from .serializers import AddUserToRoomSerializer, RoomNameSerializer, RoomSerializer, MessageSerializer, SignupSerializer, UserSerializer, CustomTokenObtainPairSerializer
from django.contrib.auth.hashers import check_password
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth import authenticate, get_user_model
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.permissions import AllowAny
from rest_framework.authtoken.models import Token
from django.http import JsonResponse
from rest_framework_simplejwt.views import TokenObtainPairView
import jwt
from datetime import datetime, timedelta

User = get_user_model()

class RoomCreateView(CreateAPIView):
    permission_classes = [AllowAny]
    serializer_class = RoomSerializer

class UserRoomListView(APIView):
    def get(self, request):
        # Get user_id from query parameters
        user_id = request.query_params.get('user_id')  # Adjust as per your frontend data

        if not user_id:
            return Response({"error": "User ID is required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Find all rooms where the user is associated using the Many-to-Many relationship
            rooms = Room.objects.filter(users__id=user_id)  # This uses the `users` Many-to-Many field

            # If no rooms found
            if not rooms:
                return Response({"message": "No rooms found for this user."}, status=status.HTTP_404_NOT_FOUND)

            # Serialize the room names
            serializer = RoomNameSerializer(rooms, many=True)
            
            return Response(serializer.data, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class AddUserToRoomView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        serializer = AddUserToRoomSerializer(data=request.data)
        if serializer.is_valid():
            room = serializer.save()
            return Response(
                {"message": f"User added to room {room.room_name} successfully."},
                status=status.HTTP_200_OK
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class MessageListView(ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = MessageSerializer

    def get_queryset(self):
        room_name = self.kwargs['room_name']
        return Message.objects.filter(room__name=room_name).order_by('timestamp')

class SignupView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        print("inside signup view")
        serializer = SignupSerializer(data=request.data)
        print("serializer",serializer)
        if serializer.is_valid():
            try:
                user = serializer.save()
                return Response({
                    "message": "User created successfully!",
                    "id": user.id,
                    "email": user.email
                }, status=status.HTTP_201_CREATED)
            except IntegrityError:
                return Response({"error": "Email already exists!"}, status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get('email')
        password = request.data.get('password')

        # Get the User model
        user = User.objects.filter(email=email).first()

        if user and check_password(password, user.password):
            # Generate JWT tokens
            access_token = self.create_jwt_token(user, 'access', timedelta(hours=1))  # Access token expires in 1 hour
            refresh_token = self.create_jwt_token(user, 'refresh', timedelta(days=7))  # Refresh token expires in 7 days

            # Send both tokens in response body
            return Response({
                "message": "Login successful!",
                "access_token": access_token,
                "refresh_token": refresh_token,
                "user_id": user.id,
                "email": user.email,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "username": user.username
            }, status=status.HTTP_200_OK)

        return Response({"error": "Invalid email or password"}, status=status.HTTP_401_UNAUTHORIZED)

    def create_jwt_token(self, user, token_type, expiration_time):
        """
        Generates a JWT token (either access or refresh token).
        :param user: The user object to embed in the token.
        :param token_type: Either 'access' or 'refresh' to distinguish token type.
        :param expiration_time: Expiration time for the token (timedelta).
        """
        # Create the payload with user information
        payload = {
            "user_id": user.id,
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "username": user.username,
            "token_type": token_type,  # To distinguish between access and refresh token
            "exp": datetime.utcnow() + expiration_time,  # Set expiration time
            "iat": datetime.utcnow()  # Issued at
        }

        # Secret key to sign the JWT (ensure to keep it secret and secure)
        secret_key = 'your_secret_key'  # Replace with your actual secret key

        # Create JWT token
        token = jwt.encode(payload, secret_key, algorithm='HS256')

        return token


class UserListView(APIView):
    # permission_classes = [IsAuthenticated]
    def get(self, request):
        users = get_user_model().objects.all()
        serializer = UserSerializer(users, many=True)
        return Response(serializer.data)
