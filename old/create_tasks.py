from django_celery_beat.models import PeriodicTask, IntervalSchedule        # , CrontabSchedule
from django.db.models import F, Q
import pytz


def run():
    schedule, _ = IntervalSchedule.objects.get_or_create(
        every=10,
        period=IntervalSchedule.SECONDS
    )

    t1 = PeriodicTask.objects.get_or_create(
        interval=schedule,
        name="Meraki Dashboard Sync",
        task="sync.tasks.task_dashboard",
        args=""
    )

    t2 = PeriodicTask.objects.get_or_create(
        interval=schedule,
        name="ISE Server Sync",
        task="sync.tasks.task_ise",
        args=""
    )

    # schedule, _ = CrontabSchedule.objects.get_or_create(
    #     minute='30',
    #     hour='*',
    #     day_of_week='*',
    #     day_of_month='*',
    #     month_of_year='*',
    #     timezone=pytz.timezone('America/Chicago')
    # )

    t3 = PeriodicTask.objects.get_or_create(
        # crontab=schedule,
        interval=schedule,
        name="pxGrid Sync",
        task="sync.tasks.task_pxgrid",
        args=""
    )

