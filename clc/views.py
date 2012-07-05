from django.http import HttpResponse, Http404, HttpResponseRedirect
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render_to_response, redirect
from django import forms
from django.db import IntegrityError
from django.db.models import Count
from clc.models import *
from django.contrib import auth 
from django.template import RequestContext
from django.utils.translation import ugettext_lazy as _, ugettext as __, get_language
from django.forms.util import ErrorList

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import Header

import datetime
from os import getenv

class SignupForm(forms.Form):
    username = forms.CharField(label=_("User name"), widget=forms.TextInput, help_text=_("Enter the username you wish to use (This is public)"))
    email = forms.EmailField(label=_("Email"), help_text=_("Enter your email address (We keep it private)"))
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
        fields = ('description','category')
    due_date = forms.DateField(required=False, label=_("Due date YYYY-MM-DD (optional)"))
    hidden = forms.CharField(widget=forms.HiddenInput, initial="challenge")
    
def message_render(request, message):
    return render_to_response(
        'message.html', {'message':_(message)},  context_instance=RequestContext(request)
    )

def display(request, list_name):
    list_name = list_name.lower()
    try:
        cl = ChallengeList.objects.get(name=list_name)
    except ChallengeList.DoesNotExist:
        return render_to_response('message.html', {'message':_("Sorry but this challenge list does not exist. Want to create it?<a href='/'>Click here.</a>")}, context_instance=RequestContext(request))
        
    challenge_instances = ChallengeInstance.objects.filter(challenge_list=cl).order_by("challenge__category")
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
        if mine or cl in friends:
            friend = True

    if mine:
        header = _("Your challenge list")
    else:
        header = _("%(name)s's challenge list") % {'name':cl.owner.username.title()}

    challenge_form = ChallengeForm()
    login_form = LoginForm()
    return render_to_response(
        'display.html', locals(), context_instance=RequestContext(request)
    )


def reset_password(request, list_name):
    try:
        user = auth.models.User.objects.get(username=list_name)
    except auth.models.User.DoesNotExist:
        return message_render(request, _("Sorry, but this user does not exist."))
    authkey = request.GET.get('authkey', None)
    if not authkey:
        return message_render(request, _("Sorry, but the authentication key is missing."))
    if authkey != user.password.split('$')[-1]:
        return message_render(request, _("Sorry, but the authentication key is wrong."))
    if request.method == 'GET':
        signup_form = SignupForm({'username':user.username, 'email':user.email, 'hidden':'signup'})
        signup_form._errors = {}
    elif request.method == 'POST':
        signup_form = SignupForm(request.POST)
        if signup_form.is_valid():
            password = request.POST['password']
            password2 = request.POST['password2']
            if password == password2:
                user.set_password(password)
                user.save()
                user = auth.authenticate(username=user.username, password=password)
                if user is not None:
                    if user.is_active:
                        auth.login(request, user)
                        return HttpResponseRedirect('/'+user.username)
                    else:
                        return message_render(request, _("Sorry, but this account is disabled."))
                else:
                    return message_render(request, _("Sorry, but this account is invalid."))
            else:
                signup_form._errors['password'] = signup_form._errors['password2'] = ErrorList((_('passwords mismatch'),)) 
    return render_to_response('reset_password.html', locals(), context_instance=RequestContext(request))


def send_password(request):
    if request.method != 'POST':
        return HttpResponse(__("You should try a POST request"))
    if "email" in request.POST:
        email = request.POST["email"]
        text_template = __("""\
Hi %(username)s,

You couldn't remember your password. That's ok.

Please click the link below to set a new one:
http://www.challengelistcreator.com/reset_password/%(username)s?authkey=%(authkey)s

Have fun,

The webmaster at challenge list creator.
""")

        html_template = __("""\
<html><body>
<a href=http://www.challengelistcreator.com style="border:0;" ><img src="http://www.challengelistcreator.com/media/images/logo.png" /></a><br/>
<br/>
Hi %(username)s,<br/>
<br/>
You couldn't remember your password. That's ok.<br/>
<br/>
<b>Please click the link below to set a new one:</b><br/>
<a href='http://www.challengelistcreator.com/reset_password/%(username)s?authkey=%(authkey)s'>Reset your password</a><br/>
<br/>
Have fun,<br/>
<br/>
The webmaster at challenge list creator.<br/>
<br/>
</body></html>
""")
        admin_email = getenv('ADMIN_EMAIL')
        try:
            user = auth.models.User.objects.get(email=email)
        except auth.models.User.DoesNotExist, e:
            return HttpResponse(str(e))
        d = {'username':user.username, 'authkey':user.password.split('$')[-1]}
        text = text_template % d
        html = html_template % d
        msg = MIMEMultipart('alternative')
        part1 = MIMEText(text.encode("utf-8"), "plain", "utf-8")
        part2 = MIMEText(html.encode("utf-8"), "html", "utf-8")
        msg.attach(part1)
        msg.attach(part2)
        msg['From'] = admin_email
        msg['To'] = email
        msg['Subject'] = Header(__("You have asked to reset your password"), 'utf-8')
        smtp = smtplib.SMTP(getenv('SMTP_SERVER'))
        smtp.login(getenv('SMTP_USERNAME'), getenv('SMTP_PASSWORD'))
        try:
            smtp.sendmail(
                msg['From'],
                msg['To'],
                msg.as_string()
            )
        except e:
            return HttpResponse(str(e))
        else:
            return HttpResponse(True)

        finally:
            if smtp:
                f = open("/tmp/msg", "w")
                f.write(msg.as_string())
                f.close()
                smtp.quit()
    else:
        return HttpResponse("email missing in POST arguments")

@login_required
def delete(request):
    if request.method != 'POST':
        return HttpResponse(__("You should try a POST request"))

    if "challenge_instance" in request.POST:
        id = request.POST["challenge_instance"]
        ci = ChallengeInstance.objects.get(pk=id)
        ci.delete()
        return HttpResponse(id)
    elif "friend" in request.POST:
        id = request.POST["friend"]
        my_cl = ChallengeList.objects.get(owner=request.user)
        friend = my_cl.friends.get(owner=id)
        my_cl.friends.remove(friend)
        return HttpResponse(id)
    else:
        return HttpResponse(0)

@login_required
def save(request):
    if request.method != 'POST':
        return HttpResponse(__("You should try a POST request"))

    if "challenge_instance" in request.POST:
        ci = ChallengeInstance.objects.get(id=request.POST["challenge_instance"])
        if "progress" in request.POST:
            ci.progress = int(request.POST["progress"])
        if "due_date" in request.POST:
            ci.due_date = datetime.date(*map(int, request.POST["due_date"].split("-")))
        ci.save()
        return HttpResponse(request.POST["challenge_instance"])

def send(request):
    if request.method != 'POST':
        return HttpResponse(__("You should try a POST request"))
    email = request.POST.get("email", "Not specified.")
    if not email:
        email = 'anonymous'
    message = request.POST.get("message", "Not specified.")
    if message == "":
        message = "Empty message."
    mime_msg = MIMEText(message.encode("utf-8"), "plain", "utf-8")
    admin_email = getenv('ADMIN_EMAIL')
    mime_msg['From'] = admin_email
    mime_msg['To'] = admin_email
    mime_msg['Subject'] = "[CLC] Message from %s" % email
    smtp = smtplib.SMTP(getenv('SMTP_SERVER'))
    smtp.login(getenv('SMTP_USERNAME'), getenv('SMTP_PASSWORD'))
    smtp.sendmail(
        admin_email,
        admin_email,
        mime_msg.as_string()
    )
    smtp.quit()
    return HttpResponse(0)

@login_required
def add(request):
    if request.method != 'POST':
        return HttpResponse(__("You should try a POST request"))
    post = {}
    for key, value in request.POST.items():
        if value == "":
            post[key] = None
        else:
            post[key] = value

    hidden = post.get("hidden", False)
    cl = ChallengeList.objects.get(owner=request.user)
    if hidden == "challenge":
        try:
            c = Challenge.objects.get(description=post["description"])
        except Challenge.MultipleObjectsReturned:
            # Quick fix until database integrity is guaranteed
            c = Challenge.objects.filter(description=post["description"])[0]
        except Challenge.DoesNotExist:
            try:
                category = Category.objects.get(id=post["category"])
            except Category.DoesNotExist:
                category = None
            c = Challenge(
                description=post["description"],
                category=category,
                language=get_language(),
            )
            c.save()
        ci = ChallengeInstance(
            challenge=c,
            challenge_list=cl,
            due_date=post.get("due_date", None),
        )
        ci.save()
        return HttpResponse(ci.id)
    elif hidden == "challenge_instance":
        original_ci = ChallengeInstance.objects.get(id=post["challenge_instance"])
        copy_ci = ChallengeInstance(
            challenge = original_ci.challenge,
            challenge_list = cl,
            origin = original_ci,
        )
        copy_ci.save()
        return HttpResponse(original_ci.id)
    elif hidden == "friend":
        friend_cl = ChallengeList.objects.get(name=post["name"])
        cl.friends.add(friend_cl)
        return HttpResponse("ok")
    return HttpResponse(0)

def login(request):
    login_form = None
    if request.method == 'POST':
        login_form = LoginForm(request.POST)
        if login_form.is_valid():
            username = request.POST['username'].lower()
            password = request.POST['password']
            user = auth.authenticate(username=username, password=password)
            if user is not None:
                if user.is_active:
                    auth.login(request, user)
                    return HttpResponse("ok;" + _("Login successful."))
                else:
                    return HttpResponse("error;" + _("Disabled account."))
            else:
                return HttpResponse("error;" + _("Invalid username and/or password."))
        else:
            return HttpResponse("error;" + _("Invalid post data."))
    else:
        return HttpResponse("error;" + _("You should try a post request."))

def index(request):
    signup_form = login_form = None
    logged_in = request.user.is_authenticated()
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
                if len(auth.models.User.objects.filter(email=email)) == 0:
                    try:
                        user = auth.models.User.objects.create_user(username, email, password)
                    except IntegrityError:
                        user = auth.authenticate(username=username, password=password)
                        if not user:
                            signup_form._errors['username'] = ErrorList((_("A user with the same name already exists. But the password you entered did not match."),))
                            valid_form = False
                    else:
                        user = auth.authenticate(username=username, password=password)
                else:
                    signup_form._errors['email'] = ErrorList((_("Email already exists."),))
                    valid_form = False
                if valid_form:
                    try:
                        cl = user.challenge_list
                    except ChallengeList.DoesNotExist:
                        cl = ChallengeList(owner=user, name=user.username)
                        cl.save()
        if valid_form:
            if user is not None:
                if user.is_active:
                    auth.login(request, user)
                    return HttpResponseRedirect(request.GET.get("next", user.username))
                else:
                    login_form._errors['username'] = ErrorList((_("Disabled account."),))
            else:
                 login_form._errors['password'] = ErrorList((_("Invalid username and/or password."),))
            
    if not login_form:
        login_form = LoginForm()
    if not signup_form:
        signup_form = SignupForm()
    challenges = Challenge.objects.filter(language=get_language()).annotate(num_ci=Count('instances')).order_by('-num_ci').all()[:10]
    #.order_by("-id")[:20]
    return render_to_response('index.html', locals(), context_instance=RequestContext(request))

def logout(request):
    auth.logout(request)
    return HttpResponseRedirect(request.GET.get("next","/")) 

