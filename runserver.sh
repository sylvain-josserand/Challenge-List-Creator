#!/bin/bash
SMTP_SERVER=<your smtp server>
SMTP_USERNAME=<your smtp username>
SMTP_PASSWORD=<your smtp password>
DJANGO_MEA=True
ADMIN_EMAIL=<admin email where suggestions and notifications are received>
./manage.py runserver
