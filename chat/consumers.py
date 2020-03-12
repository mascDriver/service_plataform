from django.contrib.auth.models import User
from asgiref.sync import async_to_sync
from channels.generic.websocket import WebsocketConsumer
import json
from .models import Message, Room, Chat
from django.db.models import Count
from .scraper import main, read_last_in_message, send_msg
import datetime

class ChatConsumer(WebsocketConsumer):
    def fetch_room(self, data):
        chats = list(Chat.objects.filter(user=data['from']).values('room__room_name','user').annotate(dcount=Count('room')))
        result = []
        for chat in chats:
            result.append(chat)
        ctx = {
            'command': 'room',
            'room': result,
        }
        self.send(text_data=json.dumps(ctx))

    def open_wpp(self,data):
        self.drive, self.session_id, self.url = main()

    def fetch_messages_wpp(self, data):
        msg, emoji, user, timestamp = read_last_in_message(self.session_id, self.url)
        if User.objects.filter(username=user):
            author_user = User.objects.get(username=user)
        else:
            author_user = User(username=user)
            author_user.set_password(user)
            author_user.save()
        if Room.objects.filter(room_name=data.get('room',''), user=author_user.username):
            room = Room.objects.get(room_name=data.get('room', ''), user=author_user.username)
        else:
            room = Room.objects.create(room_name=data.get('room', ''), user=author_user.username)
        # h = datetime.time(int(timestamp.split(':')[0]), int(timestamp.split(':')[1]))
        # time = datetime.datetime.now()
        # time_st = datetime.datetime.combine(time,h)
        # print(time.strftime("%Y-%d-%m %H:%M:%S", time.strptime(timestamp, '%I:%M%p')))
        # print(datetime.strptime(parse_date(timestamp), "%Y-%m-%d").date())
        if Message.objects.filter(author=author_user, room=room).exists():
            last_msg = Message.objects.filter(author=author_user, room=room).all().last()
            if not (last_msg.content == msg and last_msg.author == author_user and last_msg.room == room):
                message = Message.objects.create(author=author_user,
                                                 content=msg, room=room)

                Chat.objects.create(room=room, message=message, user=author_user.username)
                ctx = {
                    'command': 'wpp',
                    'user': message.author.username,
                    'msg': message.content,
                }
                self.send_message(ctx)
        else:
            message = Message.objects.create(author=author_user,
                                             content='Inicio', room=room)
            Chat.objects.create(room=room, message=message, user=author_user.username)

    def fetch_messages(self, data):
        messages = Chat.objects.filter(room__room_name=data.get('room','')).all().order_by('-id')[:10]
        last_order = reversed(messages)

        content = {
            'command': 'messages',
            'messages': self.messages_to_json(last_order),
        }
        self.send_message(content)


    def new_messages(self, data):
        author = data['from']
        if User.objects.filter(username=author):
            author_user = User.objects.get(username=author)
        else:
            author_user = User(username=author)
            author_user.set_password(author)
            author_user.save()
        room = Room.objects.get(room_name=data['roomName'], user=author_user.username)

        message = Message.objects.create(author=author_user,
                                         content=data['message'],room=room)
        Chat.objects.get_or_create(room=room, message=message, user=data['from'])
        content = {
            'command': 'new_message',
            'message': self.message_to_json(message),
        }
        send_msg(self.session_id, self.url, data['message'])
        return self.send_chat_message(content)

    def messages_to_json(self, messages):
        result = []
        for message in messages:
            result.append(self.message_to_json(message))

        return result

    def message_to_json(self, message):
        try:
            ctx = {
                'author': message.user,
                'content': message.message.content,
                'timestamp': str(message.message.timestamp),
            }
            return ctx
        except AttributeError:
            ctx = {
                'author': message.author.username,
                'content': message.content,
                'timestamp': str(message.timestamp),
            }
            return ctx

    commands = {
        'fetch_messages': fetch_messages,
        'new_message': new_messages,
        'fetch_room': fetch_room,
        'open_wpp': open_wpp,
        'fetch_messages_wpp': fetch_messages_wpp
    }

    def connect(self):
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.room_group_name = 'chat_%s' % self.room_name

        # Join room group
        async_to_sync(self.channel_layer.group_add)(
            self.room_group_name,
            self.channel_name
        )

        self.accept()

    def disconnect(self, close_code):
        # Leave room group
        async_to_sync(self.channel_layer.group_discard)(
            self.room_group_name,
            self.channel_name
        )

    # Receive message from WebSocket
    def receive(self, text_data):
        data = json.loads(text_data)
        self.commands[data['command']](self, data)

    def send_chat_message(self, message):
        # Send message to room group
        async_to_sync(self.channel_layer.group_send)(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message': message
            }
        )
    def send_message(self, message):
        self.send(text_data=json.dumps(message))

    # Receive message from room group
    def chat_message(self, event):
        message = event['message']

        # Send message to WebSocket
        self.send(text_data=json.dumps(message))