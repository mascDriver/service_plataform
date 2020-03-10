from django.contrib.auth.models import User
from asgiref.sync import async_to_sync
from channels.generic.websocket import WebsocketConsumer
import json
from .models import Message, Room, Chat
from django.db.models import Count
from .scraper import main


class ChatConsumer(WebsocketConsumer):
    def __init__(self, *args, **kwargs):
        self.driver = ''
        self.previous_in_message = ''
        previous_in_message, driver = main(driver=self.driver)
        ChatConsumer.__init__(self)
        super().__init__(*args, **kwargs)

    def fetch_room(self, data):
        chats = list(Chat.objects.filter(user=data['from']).values('room__room_name','user').annotate(dcount=Count('room')))
        result = []
        for chat in chats:
            result.append(chats)
        ctx = {
            'command': 'room',
            'room': result,
        }
        self.send(text_data=json.dumps(ctx))


    def fetch_messages(self, data):
        main(self.driver)
        print(self.driver, self.previous_in_message)
        messages = Chat.objects.filter(room__room_name=data.get('room','')).all().order_by('-id')[:10]
        last_order = reversed(messages)
        content = {
            'command': 'messages',
            'messages': self.messages_to_json(last_order)
        }
        self.send_message(content)

    def new_messages(self, data):
        author = data['from']
        room = Room.objects.get(room_name=data['roomName'], user=data['from'])
        author_user = User.objects.filter(username=author)[0]
        message = Message.objects.create(author=author_user,
                                         content=data['message'],room=room)
        Chat.objects.get_or_create(room=room, message=message, user=data['from'])

        content = {
            'command': 'new_message',
            'message': self.message_to_json(message)
        }
        return self.send_chat_message(content)

    def messages_to_json(self, messages):
        result = []
        for message in messages:
            result.append(self.message_to_json(message))
        return result

    def message_to_json(self, message):
        return {
            'author': message.user,
            'content': message.message.content,
            'timestamp': str(message.message.timestamp)
        }

    commands = {
        'fetch_messages': fetch_messages,
        'new_message': new_messages,
        'fetch_room': fetch_room
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