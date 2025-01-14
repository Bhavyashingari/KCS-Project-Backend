from sqlite3 import IntegrityError
from django.shortcuts import render
from rest_framework.generics import ListCreateAPIView, ListAPIView
from .serializers import AddMessageSerializer, AddUserToRoomSerializer, RoomNameSerializer, RoomSerializer, SignupSerializer, UserSerializer, MessageSerializer
from rest_framework.generics import CreateAPIView, ListAPIView
from django.contrib.auth.hashers import check_password
from django.contrib.auth import get_user_model
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, AllowAny
from .models import Room, Message
from rest_framework_simplejwt.tokens import RefreshToken
from msal import ConfidentialClientApplication
import jwt
from datetime import datetime, timedelta
from django.conf import settings

User = get_user_model()


class RoomCreateView(CreateAPIView):
    permission_classes = [AllowAny]
    serializer_class = RoomSerializer


class UserRoomListView(APIView):
    def get(self, request):
        user_id = request.query_params.get("user_id")

        if not user_id:
            return Response({"error": "User ID is required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            rooms = Room.objects.filter(users__id=user_id)
            if not rooms:
                return Response({"message": "No rooms found for this user."}, status=status.HTTP_404_NOT_FOUND)
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
                status=status.HTTP_200_OK,
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class MessageListView(ListAPIView):
    """
    View to fetch messages for a specific room by room_id in descending order.
    """
    permission_classes = [IsAuthenticated]
    serializer_class = MessageSerializer

    def get_queryset(self):
        room_id = self.kwargs['room_id']  # Get room_id from the URL
        return Message.objects.filter(room__id=room_id).order_by('-timestamp')  # Descending order

class SignupView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = SignupSerializer(data=request.data)
        if serializer.is_valid():
            try:
                user = serializer.save()
                return Response(
                    {
                        "message": "User created successfully!",
                        "id": user.id,
                        "email": user.email,
                    },
                    status=status.HTTP_201_CREATED,
                )
            except IntegrityError:
                return Response({"error": "Email already exists!"}, status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        token = request.data.get("token")  # Azure AD token from frontend

        if not token:
            return Response({"error": "Token is required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            decoded_token = self.validate_azure_token(token)

            if not decoded_token:
                return Response({"error": "Invalid Azure AD token."}, status=status.HTTP_401_UNAUTHORIZED)

            email = decoded_token.get("email")
            first_name = decoded_token.get("given_name")
            last_name = decoded_token.get("family_name")

            user, created = User.objects.get_or_create(
                email=email,
                defaults={
                    "first_name": first_name,
                    "last_name": last_name,
                    "username": email.split("@")[0],
                },
            )

            access_token = self.create_jwt_token(user, "access", timedelta(hours=1))
            refresh_token = self.create_jwt_token(user, "refresh", timedelta(days=7))

            return Response(
                {
                    "message": "Login successful!",
                    "access_token": access_token,
                    "refresh_token": refresh_token,
                    "user_id": user.id,
                    "email": user.email,
                    "first_name": user.first_name,
                    "last_name": user.last_name,
                    "username": user.username,
                },
                status=status.HTTP_200_OK,
            )

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def validate_azure_token(self, token):
        try:
            client_app = ConfidentialClientApplication(
                settings.AZURE_CLIENT_ID,
                authority=f"https://login.microsoftonline.com/{settings.AZURE_TENANT_ID}",
                client_credential=settings.AZURE_CLIENT_SECRET,
            )

            result = client_app.acquire_token_on_behalf_of(token, scopes=["User.Read"])
            if "id_token_claims" in result:
                return result["id_token_claims"]
            return None
        except Exception as e:
            print(f"Azure token validation error: {e}")
            return None

    def create_jwt_token(self, user, token_type, expiration_time):
        payload = {
            "user_id": user.id,
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "username": user.username,
            "token_type": token_type,
            "exp": datetime.utcnow() + expiration_time,
            "iat": datetime.utcnow(),
        }
        secret_key = settings.SECRET_KEY
        token = jwt.encode(payload, secret_key, algorithm="HS256")
        return token


class UserListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        users = get_user_model().objects.all()
        serializer = UserSerializer(users, many=True)
        return Response(serializer.data)


class AddMessageToRoomView(APIView):
    # permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        serializer = AddMessageSerializer(data=request.data)
        if serializer.is_valid():
            try:
                message = serializer.save()
                return Response({
                    "message": "Message added successfully.",
                    "message_id": message.message_id,
                    "room_id": message.room.id,
                    "content": message.content,
                    "timestamp": message.timestamp
                }, status=status.HTTP_201_CREATED)
            except Exception as e:
                return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)