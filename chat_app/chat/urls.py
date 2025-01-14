from django.urls import path
from .views import AddMessageToRoomView, AddUserToRoomView, RoomCreateView, MessageListView, SignupView, LoginView, UserListView, UserRoomListView
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)


urlpatterns = [
    # path('api/rooms/', RoomListCreateView.as_view(), name='room-list-create'),
    path('api/rooms/create/', RoomCreateView.as_view(), name='create-room'),
    path('api/rooms/add-user/', AddUserToRoomView.as_view(), name='add-user-to-room'),
    path('api/messages/<str:room_id>/', MessageListView.as_view(), name='message-list'),
    path('api/signup/', SignupView.as_view(), name='signup'),
    path('api/login/', LoginView.as_view(), name='login'),
    path('api/users/list/', UserListView.as_view(), name='user-list'),
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/user/rooms/', UserRoomListView.as_view(), name="user_rooms"),
    path('api/add-message/', AddMessageToRoomView.as_view(), name='add-message'),
]
