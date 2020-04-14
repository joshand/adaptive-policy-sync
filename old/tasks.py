from celery import Celery
from celery.schedules import crontab
from celery import shared_task
from scripts.dashboard_monitor import *
from scripts.ise_monitor import *
from scripts.pxgrid_websocket import *
from django_celery_beat.models import PeriodicTask


app = Celery()


@app.task
def task_dashboard():
    sync_dashboard()


@app.task
def task_ise():
    sync_ise()


@app.task
def task_pxgrid():
    tasklist = PeriodicTask.objects.filter(name__iexact="pxGrid Sync")
    t = tasklist[0]
    t.enabled = False
    t.save()
    sync_pxgrid()
