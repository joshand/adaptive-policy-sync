import atexit
from apscheduler.schedulers.background import BackgroundScheduler
from sync.models import *
from scripts.dblog import *


def cleanup():
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
    # Enable the job scheduler to run schedule jobs
    cron = BackgroundScheduler()

    # Explicitly kick off the background thread
    cron.start()
    cron.remove_all_jobs()
    job0 = cron.add_job(cleanup)
    job1 = cron.add_job(cleanup, 'interval', seconds=60)

    # Shutdown your cron thread if the web process is stopped
    atexit.register(lambda: cron.shutdown(wait=False))

