from django.urls import path
from .views import room, Login, Index, Create

urlpatterns = [
    path('', Index.as_view(), name='index'),
    path('room/<str:room_name>/', room, name='room'),
    path('login/', Login.as_view(), name='login'),
    path('create/', Create.as_view(), name='create')

]