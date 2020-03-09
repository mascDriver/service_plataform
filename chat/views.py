from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.views.generic import CreateView, TemplateView
from django.contrib.auth.models import User
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import login as auth_login
from django.contrib.auth.views import LoginView


class Index(LoginRequiredMixin, TemplateView):
    login_url = 'login'
    template_name = 'chat/index.html'


@login_required
def room(request, room_name):
    return render(request, 'chat/room.html', {
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
        return '/'

class Login(LoginView):
    template_name = 'chat/login.html'
    redirect_field_name = 'chat/index.html'
    authentication_form = AuthenticationForm




