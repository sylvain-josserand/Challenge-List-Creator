#!/usr/bin/python
from django.core.management import setup_environ
import settings

setup_environ(settings)

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from datetime import date
from clc.models import ChallengeInstance
from os import getenv

admin_email = getenv('ADMIN_EMAIL')

emails = set()

text_template = """\
Hi %(username)s,

Some challenge of yours is due today.
Have you accomplished what you wanted?
Then congratulations!
In case some external event prevented you from fulfilling your destiny, then I sympathize.
In any case, you may update your challenge list here: http://www.challengelistcreator.com/%(username)s.

Have fun,

The webmaster at challenge list creator.
"""

html_template = """\
<html><body>
<a href=http://www.challengelistcreator.com style="border:0;" ><img src="http://www.challengelistcreator.com/media/images/logo.png" /></a><br/>
<br/>
Hi %(username)s,<br/>
<br/>
Some challenge of yours is due today.<br/>
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
"""

smtp = smtplib.SMTP(getenv('SMTP_SERVER'))
smtp.login(getenv('SMTP_USERNAME'), getenv('SMTP_PASSWORD'))
for ci in ChallengeInstance.objects.filter(due_date=date.today()):
    email = ci.challenge_list.owner.email
    if email in emails:
        continue
    else:
        emails.add(email)
    username = ci.challenge_list.owner.username
    text = text_template % {'username':username} 
    html = html_template % {'username':username} 
    msg = MIMEMultipart('alternative')
    part1 = MIMEText(text.encode("utf-8"), "plain", "utf-8")
    part2 = MIMEText(html.encode("utf-8"), "html", "utf-8")
    msg.attach(part1)
    msg.attach(part2)
    msg['From'] = admin_email
    msg['To'] = email
    msg['Subject'] = "Have you completed your challenge?"
    smtp.sendmail(
        admin_email,
        email,
        msg.as_string()
    )
smtp.quit()



