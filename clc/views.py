from django.http import HttpResponse, Http404, HttpResponseRedirect
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render_to_response, redirect
from django import forms
from django.db import IntegrityError
from clc.models import *
from django.contrib import auth 
from django.template import RequestContext
from django.utils.translation import ugettext_lazy as _, get_language
from django.forms.util import ErrorList

class SignupForm(forms.Form):
    username = forms.CharField(label=_("user name"), widget=forms.TextInput, help_text=_("Enter the username you wish to use"))
    email = forms.EmailField(label=_("email"), help_text=_("Enter your email address"))
    password = forms.CharField(label=_("password"), widget=forms.PasswordInput, help_text=_("Enter your super-secret password"))
    password2 = forms.CharField(label=_("Confirm password"), widget=forms.PasswordInput, help_text=_("Enter the same password again"))
    hidden = forms.CharField(widget=forms.HiddenInput, initial="signup")

class LoginForm(forms.Form):
    username = forms.CharField(label=_("username"), widget=forms.TextInput, help_text=_("Enter your username"))
    password = forms.CharField(label=_("password"), widget=forms.PasswordInput, help_text=_("Enter your password"))
    hidden = forms.CharField(widget=forms.HiddenInput, initial="login")

class ChallengeForm(forms.ModelForm):
    class Meta:
        model = Challenge
        exclude = ('challenge_list','progress')

def display(request, list_name):
    challenges = Challenge.objects.filter(challenge_list__name=list_name).order_by("category")
    cl = ChallengeList.objects.get(name=list_name)
    if request.method == 'POST':
        challenge_form = ChallengeForm(request.POST)
        if challenge_form.is_valid():
            try:
                category = Category.objects.get(id=request.POST["category"])
            except Category.DoesNotExist:
                category = None
            c = Challenge(
                challenge_list=cl,
                description=request.POST["description"],
                category=category,
            )
            c.save()
    else:
        challenge_form = ChallengeForm()
    lang=get_language()
    return render_to_response(
        'display.html', locals(), context_instance=RequestContext(request)
    )

@login_required
def delete(request):
    if request.method == 'POST':
        if "challenge" in request.POST:
            c = Challenge.objects.get(id=request.POST["challenge"])
            c.delete()
            return HttpResponse(request.POST["challenge"])
    return HttpResponse("You should try a POST request")

@login_required
def save(request):
    if request.method == 'POST':
        if "challenge" in request.POST:
            c = Challenge.objects.get(id=request.POST["challenge"])
            if "progress" in request.POST:
                c.progress = int(request.POST["progress"])
            c.save()
            return HttpResponse(request.POST["challenge"])
    return HttpResponse("You should try a POST request")

def index(request):
    signup_form = login_form = None
    if request.method == 'POST':
        valid_form = False
        if request.POST['hidden'] == "login":
            login_form = LoginForm(request.POST)
            if login_form.is_valid():
                username = request.POST['username']
                password = request.POST['password']
                user = auth.authenticate(username=username, password=password)
                valid_form = True
        elif request.POST['hidden'] == "signup":
            signup_form = SignupForm(request.POST)
            if signup_form.is_valid():
                valid_form = True
            password = request.POST['password']
            password2 = request.POST['password2']
            if password != password2:
                signup_form._errors['password'] = signup_form._errors['password2'] = ErrorList(('passwords mismatch',)) 
                valid_form = False
            if valid_form:
                username = request.POST['username']
                email = request.POST['email']
                try:
                    user = auth.models.User.objects.create_user(username, email, password)
                except IntegrityError:
                    user = auth.authenticate(username=username, password=password)
                    if not user:
                        return HttpResponse("A user with the same name already exists. But the password you entered is invalid.")
                user = auth.authenticate(username=username, password=password)
                valid_form = True
        if valid_form:
            if user is not None:
                if user.is_active:
                    auth.login(request, user)
                    return HttpResponseRedirect("/")
                else:
                    return HttpResponse("Disabled account.")
            else:
                return HttpResponse("Invalid login.")
            
    elif request.user.is_authenticated():
        try:
            cl = request.user.challenge_list
        except ChallengeList.DoesNotExist:
            cl = ChallengeList(owner=request.user, name=request.user.username)
            cl.save()
        return HttpResponseRedirect(cl.name)
    if not login_form:
        login_form = LoginForm()
    if not signup_form:
        signup_form = SignupForm()
    return render_to_response('index.html', {"login_form":login_form, "signup_form":signup_form}, context_instance=RequestContext(request))

def logout(request):
    auth.logout(request)
    return HttpResponseRedirect("/") 

