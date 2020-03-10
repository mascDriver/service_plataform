from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.views.generic import CreateView, TemplateView
from django.contrib.auth.models import User
from .models import Chat, Room
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import login as auth_login
from django.contrib.auth.views import LoginView


class Index(LoginRequiredMixin, TemplateView):
    login_url = 'login'
    # model = Room
    template_name = 'chat/index.html'

    # def dispatch(self, request, *args, **kwargs):
    #     # Sets a test cookie to make sure the user has cookies enabled
    #     request.session.set_test_cookie()
    #
    #     return super(Index, self).dispatch(request, *args, **kwargs)
    #
    # def get_object(self, **kwargs):
    #     print(self.request.user., 'a')
    #
    #     return Room.objects.get(author=self.request.user.id)


@login_required
def room(request, room_name):
    room = Room.objects.get_or_create(room_name=room_name, user=request.user.username)
    return render(request, 'chat/room.html', {
        'room': room,
        'room_name': room_name,
        'username': request.user.username
    })


class Create(CreateView):
    template_name = 'chat/create.html'
    model = User
    form_class = UserCreationForm
    success_url = reverse_lazy('index')

    def get_success_url(self):
        # login the person
        self.object.backend = 'django.contrib.auth.backends.ModelBackend'
        auth_login(self.request, self.object)
        # now return the success url
        return reverse_lazy('index')

class Login(LoginView):
    template_name = 'chat/login.html'
    redirect_field_name = 'chat/index.html'
    authentication_form = AuthenticationForm




