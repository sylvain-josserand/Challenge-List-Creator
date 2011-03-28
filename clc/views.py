from django.http import HttpResponse, Http404, HttpResponseRedirect
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render_to_response, redirect
from django import forms
from django.db import IntegrityError
from clc.models import *
from django.contrib import auth 
from django.template import RequestContext
from django.utils.translation import ugettext_lazy as _, ugettext as __, get_language
from django.forms.util import ErrorList

class SignupForm(forms.Form):
    username = forms.CharField(label=_("User name"), widget=forms.TextInput, help_text=_("Enter the username you wish to use"))
    email = forms.EmailField(label=_("Email"), help_text=_("Enter your email address"))
    password = forms.CharField(label=_("Password"), widget=forms.PasswordInput, help_text=_("Enter your super-secret password"))
    password2 = forms.CharField(label=_("Password confirmation"), widget=forms.PasswordInput, help_text=_("Enter the same password again"))
    hidden = forms.CharField(widget=forms.HiddenInput, initial="signup")

class LoginForm(forms.Form):
    username = forms.CharField(label=_("Username"), widget=forms.TextInput, help_text=_("Enter your username"))
    password = forms.CharField(label=_("Password"), widget=forms.PasswordInput, help_text=_("Enter your password"))
    hidden = forms.CharField(widget=forms.HiddenInput, initial="login")

class ChallengeForm(forms.ModelForm):
    class Meta:
        model = Challenge
        exclude = ('challenge_list','progress')
    hidden = forms.CharField(widget=forms.HiddenInput, initial="challenge")

class CategoryForm(forms.Form):
    name = forms.CharField(label=_("Name"), widget=forms.TextInput, help_text=_("Enter the category name"))
    hidden = forms.CharField(widget=forms.HiddenInput, initial="category")

def display(request, list_name):
    list_name = list_name.lower()
    try:
        cl = ChallengeList.objects.get(name=list_name)
    except ChallengeList.DoesNotExist:
        return render_to_response('base.html', {'content':_("Sorry but this challenge list does not exist. Want to create it?<a href='/'>Click here.</a>")})
        
    challenges = Challenge.objects.filter(challenge_list=cl).order_by("category")
    # Is user logged in?
    logged_in = request.user.is_authenticated()
    
    # Is this my list?
    mine = request.user == cl.owner
    
    # My friends' lists
    if logged_in:
        if mine:
            my_cl = cl
        else:
            my_cl = ChallengeList.objects.get(owner=request.user)
        friends = my_cl.friends.all()

        friend = False
        if mine:
            friend = True
        elif cl in friends:
            friend = True

    if mine:
        categories = Category.objects.filter(owner=request.user)
        header = _("Your challenge list")
    else:
        header = _("%(name)s's challenge list") % {'name':cl.owner.username.title()}

    challenge_form = ChallengeForm()
    category_form = CategoryForm() 
    return render_to_response(
        'display.html', locals(), context_instance=RequestContext(request)
    )

@login_required
def delete(request):
    if request.method != 'POST':
        return HttpResponse(__("You should try a POST request"))

    if "challenge" in request.POST:
        id = request.POST["challenge"]
        c = Challenge.objects.get(id=id)
        c.delete()
        return HttpResponse(id)
    elif "category" in request.POST:
        id = request.POST["category"]
        c = Category.objects.get(id=id)
        c.delete()
        return HttpResponse(id)
    elif "friend" in request.POST:
        id = request.POST["friend"]
        my_cl = ChallengeList.objects.get(owner=request.user)
        friend = my_cl.friends.get(owner=id)
        my_cl.friends.remove(friend)
        return HttpResponse(id)

@login_required
def save(request):
    if request.method != 'POST':
        return HttpResponse(__("You should try a POST request"))

    if "challenge" in request.POST:
        c = Challenge.objects.get(id=request.POST["challenge"])
        if "progress" in request.POST:
            c.progress = int(request.POST["progress"])
        c.save()
        return HttpResponse(request.POST["challenge"])

@login_required
def add(request):
    if request.method != 'POST':
        return HttpResponse(__("You should try a POST request"))
        
    obj = request.POST.get("hidden", False)
    cl = ChallengeList.objects.get(owner=request.user)
    if obj == "challenge":    
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
        return HttpResponse(c.id)
    elif obj == "category":    
        c = Category(
            owner=request.user, 
            name=request.POST["name"],
            red=request.POST["red"],
            green=request.POST["green"],
            blue=request.POST["blue"],
        )
        c.save()
        return HttpResponse(c.id)
    elif obj == "friend":
        friend_cl = ChallengeList.objects.get(name=request.POST["name"])
        cl.friends.add(friend_cl)
        return HttpResponse("ok")

    elif "challenge" in request.POST:
    # Challenge copy
        c = Challenge.objects.get(id=request.POST["challenge"])
        new_c = Challenge(
            challenge_list=cl,
            description=c.description,
            category=c.category,
        )
        new_c.save()
        return HttpResponse(new_c.id)

        
    return HttpResponse(0)

def index(request):
    signup_form = login_form = None
    if request.method == 'POST':
        valid_form = False
        if request.POST['hidden'] == "login":
            login_form = LoginForm(request.POST)
            if login_form.is_valid():
                username = request.POST['username'].lower()
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
                signup_form._errors['password'] = signup_form._errors['password2'] = ErrorList((_('passwords mismatch'),)) 
                valid_form = False
            if valid_form:
                username = request.POST['username'].lower()
                email = request.POST['email']
                try:
                    user = auth.models.User.objects.create_user(username, email, password)
                except IntegrityError:
                    user = auth.authenticate(username=username, password=password)
                    if not user:
                        return HttpResponse(__("A user with the same name already exists. But the password you entered is invalid."))
                user = auth.authenticate(username=username, password=password)
                valid_form = True
        if valid_form:
            if user is not None:
                if user.is_active:
                    auth.login(request, user)
                    if "next" in request.GET:
                        return HttpResponseRedirect(request.GET["next"])
                    else:
                        return HttpResponseRedirect("/")
                else:
                    return HttpResponse(__("Disabled account."))
            else:
                return HttpResponse(__("Invalid login."))
            
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

