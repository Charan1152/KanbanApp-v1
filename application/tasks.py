from application.workers import celery
from datetime import datetime
from flask import current_app as app
from application.models import *

from celery.schedules import crontab
print("crontab ", crontab)


@celery.on_after_finalize.connect
def setup_periodic_tasks(sender, **kwargs):
    sender.add_periodic_task(10, send_report.s(), name='add every 10')


@celery.task()
def send_report():
    user = Users.query.all()
    for i in user:
        