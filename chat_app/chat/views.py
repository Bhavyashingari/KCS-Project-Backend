from sqlite3 import IntegrityError
from django.shortcuts import render
from rest_framework.generics import ListCreateAPIView, ListAPIView
from .models import Room, Message
from .serializers import RoomSerializer, MessageSerializer, SignupSerializer, UserSerializer, CustomTokenObtainPairSerializer
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

class RoomListCreateView(ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    queryset = Room.objects.all()
    serializer_class = RoomSerializer

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
        user = User.objects.filter(username=email).first()

        if user and check_password(password, user.password):
            # Manually create the token
            access_token = self.create_jwt_token(user)

            # Send the custom token in response body
            return Response({
                "message": "Login successful!",
                "access_token": access_token,
                "user_id": user.id,
                "email": user.email,
                "first_name": user.first_name,
                "last_name": user.last_name
            }, status=status.HTTP_200_OK)

        return Response({"error": "Invalid email or password"}, status=status.HTTP_401_UNAUTHORIZED)

    def create_jwt_token(self, user):
        # Create the payload with user information
        payload = {
            "user_id": user.id,
            "email": user.username,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "exp": datetime.utcnow() + timedelta(hours=1),  # Token expires in 1 hour
            "iat": datetime.utcnow()  # Issued at
        }

        # Secret key to sign the JWT (you can set this in your settings.py)
        secret_key = 'your_secret_key'  # Make sure to keep this secret and secure

        # Create JWT token
        token = jwt.encode(payload, secret_key, algorithm='HS256')

        return token

class UserListView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        users = get_user_model().objects.all()
        serializer = UserSerializer(users, many=True)
        return Response(serializer.data)
