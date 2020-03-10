from django.contrib.auth.models import User
from django.db import models

class Room(models.Model):
    room_name = models.CharField(verbose_name='Nome da sala', max_length=100)
    user = models.CharField(verbose_name='Usuarios', max_length=100)

    def __str__(self):
        return "{}".format(self.room_name)


class Message(models.Model):
    author = models.ForeignKey(User, related_name='author_messages', on_delete=models.CASCADE)
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    room = models.ForeignKey(Room, on_delete=models.CASCADE)

    def __str__(self):
        return self.author.username

    @staticmethod
    def last_10_messages():
        return Message.objects.order_by('-timestamp').all()[:10]

class Chat(models.Model):
    room = models.ForeignKey(Room, on_delete=models.CASCADE)
    message = models.ForeignKey(Message, on_delete=models.CASCADE)
    user = models.CharField(verbose_name='Usuarios', max_length=100)