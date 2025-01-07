from django.urls import path
from .views import RoomListCreateView, MessageListView, SignupView, LoginView, UserListView
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)


urlpatterns = [
    path('api/rooms/', RoomListCreateView.as_view(), name='room-list-create'),
    path('api/messages/<str:room_name>/', MessageListView.as_view(), name='message-list'),
    path('api/signup/', SignupView.as_view(), name='signup'),
    path('api/login/', LoginView.as_view(), name='login'),
    path('api/users/list/', UserListView.as_view(), name='user-list'),
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]
