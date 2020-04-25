# import atexit
# from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.schedulers.background import BackgroundScheduler
from django_apscheduler.jobstores import DjangoJobStore
from django_apscheduler.jobstores import register_events
from django_apscheduler.models import DjangoJobExecution

from django.utils.timezone import make_aware
import datetime
from sync.models import Task
from scripts.dblog import append_log

scheduler = BackgroundScheduler()
scheduler.add_jobstore(DjangoJobStore(), "default")


def cleanup():
    DjangoJobExecution.objects.delete_old_job_executions(3600)
    log = []
    task_types = ["ise_monitor", "dashboard_monitor", "pxgrid_websocket", "dashboard_webhook"]
    for t in task_types:
        tasks = Task.objects.filter(description=t)[:25].values_list("id", flat=True)
        Task.objects.filter(description=t).exclude(pk__in=list(tasks)).delete()
        append_log(log, "task_cleanup::", t)

    t1, _ = Task.objects.get_or_create(
        description="task_cleanup"
    )
    t1.task_data = "\n".join(log)
    t1.last_update = make_aware(datetime.datetime.now())
    t1.save()


def run():
    pass
    # # Enable the job scheduler to run schedule jobs
    # cron = BackgroundScheduler()
    #
    # # Explicitly kick off the background thread
    # cron.start()
    # cron.remove_all_jobs()
    # cron.add_job(cleanup)
    # cron.add_job(cleanup, 'interval', seconds=60)
    #
    # # Shutdown your cron thread if the web process is stopped
    # atexit.register(lambda: cron.shutdown(wait=False))


@scheduler.scheduled_job("interval", seconds=10, id="task_cleanup")
def job():
    cleanup()


register_events(scheduler)
scheduler.start()
