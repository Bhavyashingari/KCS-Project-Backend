from django.urls import path
from .views import RoomListCreateView, MessageListView

urlpatterns = [
    path('api/rooms/', RoomListCreateView.as_view(), name='room-list-create'),
    path('api/messages/<str:room_name>/', MessageListView.as_view(), name='message-list'),
]
