#!/usr/bin/python
# -*- encoding:utf-8 -*-
from django.core.management import setup_environ
import settings

setup_environ(settings)

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import Header

from datetime import date
from clc.models import ChallengeInstance
from os import getenv

from django.utils.translation import activate, ugettext as _

admin_email = getenv('ADMIN_EMAIL')

langs = {}
#langs['fr'] = translation('django', localedir="./locale", languages=['fr'])
#langs['en'] = translation('django', localedir="./locale", languages=['en'], fallback=True)

# dynamic language switching does not work with gettext translation() 
# nor with django activate()

langs['fr'] = {'text_template':u"""\
Bonjour %(username)s,

Vous aviez %(n_challenge)s à relever aujourd'hui:
%(challenges)s
Avez-vous pu accomplir votre objectif?
Dans ce cas, félicitations!
Un événement indépendant de votre volonté vous a-t-il empêché d'accomplir votre destin?
Dans tous les cas, vous pouvez mettre à jour votre liste de défis ici:
http://www.challengelistcreator.com/%(username)s.

Amusez-vous bien,

Le webmaster de challenge list creator.
""",
'html_template':u"""\
<html><body>
<a href=http://www.challengelistcreator.com style="border:0;" ><img src="http://www.challengelistcreator.com/media/images/logo.png" /></a><br/>
<br/>
Bonjour %(username)s,<br/>
<br/>
Vous aviez %(n_challenge)s à relever aujourd'hui:<br/>
%(challenges)s
Avez-vous pu accomplir votre objectif?<br/>
Dans ce cas, félicitations!<br/>
Un événement indépendant de votre volonté vous a-t-il empêché d'accomplir votre destin?<br/>
<b>Dans tous les cas, vous pouvez mettre à jour votre liste de défis ici:<a href=http://www.challengelistcreator.com/%(username)s>Votre liste de défis</a></b><br/>
<br/>
Amusez-vous bien,<br/>
<br/>
Le webmaster de challenge list creator.<br/>
<br/>
</body></html>""",
'subject':u"Avez-vous accompli votre défi?",
'subject_pl':u"Avez-vous accompli vos défis?",
'challenge':u"un défi",
'challenge_pl':u"%d défis",
}

langs['en'] = { 
'text_template':u"""\
Hi %(username)s,

You had %(n_challenge)s to complete today:
%(challenges)s
Have you accomplished what you wanted?
Then congratulations!
In case some external event prevented you from fulfilling your destiny, then I sympathize.
In any case, you may update your challenge list here: http://www.challengelistcreator.com/%(username)s.

Have fun,

The webmaster at challenge list creator.
""",
'html_template':u"""\
<html><body>
<a href=http://www.challengelistcreator.com style="border:0;" ><img src="http://www.challengelistcreator.com/media/images/logo.png" /></a><br/>
<br/>
Hi %(username)s,<br/>
<br/>
You had %(n_challenge)s to complete today:<br/>
%(challenges)s
Have you accomplished what you wanted?<br/>
Then congratulations!<br/>
In case some external event prevented you from fulfilling your destiny, then I sympathize.<br/>
<b>In any case, you may update your challenge list here: <a href=http://www.challengelistcreator.com/%(username)s>Your challenge list</a>.</b><br/>
<br/>
Have fun,<br/>
<br/>
The webmaster at challenge list creator.<br/>
<br/>
</body></html>
""",
'subject':u"Have you completed your challenge?",
'subject_pl':u"Have you completed your challenges?",
'challenge':u"a challenge",
'challenge_pl':u"%d challenges",
}
smtp = smtplib.SMTP(getenv('SMTP_SERVER'))
smtp.login(getenv('SMTP_USERNAME'), getenv('SMTP_PASSWORD'))

users = {} # will store user[lang]=[challenge_instance1, challenge_instance2, ...]
for lang in langs:
    users[lang] = {}

for ci in ChallengeInstance.objects.filter(due_date=date.today()).filter(progress__lt=100):
    user = ci.challenge_list.owner
    lang = ci.challenge.language
    if lang not in langs:
        lang = 'en'
    if user in users[lang]:
        users[lang][user].append(ci) 
    else:
        users[lang][user] = [ci,]

print users
for lang in users:
#    langs[lang].install()
    activate(lang)
    print "###"+lang+"###"

    for user, ci_list in users[lang].items():
        if len(ci_list) == 1:
            n_challenge = langs[lang]['challenge']
        else:
            n_challenge = langs[lang]['challenge_pl'] % len(ci_list)
        text = langs[lang]['text_template'] % {
            'username':user.username,
            'challenges':u'\n'.join((ci.challenge.description for ci in ci_list)),
            'n_challenge':n_challenge,
        }
        html = langs[lang]['html_template'] % {
            'username':user.username,
            'challenges':u'<ul>'+u'\n'.join((('<li><a href="http://www.challengelistcreator.com/%s">%s</a>' % (user.username, ci.challenge.description)) for ci in ci_list))+u'</ul>',
            'n_challenge':n_challenge,
        } 
        msg = MIMEMultipart('alternative')
        part1 = MIMEText(text.encode("utf-8"), "plain", "utf-8")
        part2 = MIMEText(html.encode("utf-8"), "html", "utf-8")
        msg.attach(part1)
        msg.attach(part2)
        msg['From'] = admin_email
        msg['To'] = user.email
        if len(ci_list) == 1:
            msg['Subject'] = Header(langs[lang]['subject'], 'utf-8')
        else:
            msg['Subject'] = Header(langs[lang]['subject_pl'], 'utf-8')
        smtp.sendmail(
            admin_email,
            user.email,
            msg.as_string()
        )
        print msg.as_string()
smtp.quit()



