#!/bin/bash
export SMTP_SERVER=<your smtp server>
export SMTP_USERNAME=<your smtp username>
export SMTP_PASSWORD=<your smtp password>
export ADMIN_EMAIL=<email address where suggestions and notifications are received>
export DJANGO_MEDIA=True
./manage.py runserver
