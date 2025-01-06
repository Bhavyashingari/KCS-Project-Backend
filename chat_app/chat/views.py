from django.shortcuts import render
from rest_framework.generics import ListCreateAPIView, ListAPIView
from .models import Room, Message
from .serializers import RoomSerializer, MessageSerializer, SignupSerializer, UserSerializer
from django.contrib.auth.hashers import check_password
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth import authenticate, get_user_model
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.permissions import AllowAny
from rest_framework.authtoken.models import Token

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
        serializer = SignupSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "User created successfully!"}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get('email')
        password = request.data.get('password')

        User = get_user_model()
        user = User.objects.filter(username=email).first() 

        if user and check_password(password, user.password):
            refresh = RefreshToken.for_user(user)
            access_token = str(refresh.access_token)

            return Response({
                "message": "Login successful!",
                "access_token": access_token,
                "refresh_token": str(refresh), 
            }, status=status.HTTP_200_OK)

        return Response({"error": "Invalid email or password"}, status=status.HTTP_401_UNAUTHORIZED)
    

class UserListView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        users = get_user_model().objects.all()
        serializer = UserSerializer(users, many=True)
        return Response(serializer.data)