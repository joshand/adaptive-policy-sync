import atexit
from apscheduler.schedulers.background import BackgroundScheduler
import threading
import asyncio
import sys
from sync.models import *


def run_tasks():
    # Enable the job scheduler to run schedule jobs
    cron = BackgroundScheduler()

    # Explicitly kick off the background thread
    cron.start()
    cron.remove_all_jobs()
    # Shutdown your cron thread if the web process is stopped
    atexit.register(lambda: cron.shutdown(wait=False))

    if 'runserver' not in sys.argv:
        return None
    try:
        import scripts.clean_tasks
        scripts.clean_tasks.run()
    except:
        print("#### Exception starting scheduled job: clean_tasks")

    try:
        import scripts.dashboard_monitor
        scripts.dashboard_monitor.run()
    except:
        print("#### Exception starting scheduled job: dashboard_monitor")

    try:
        import scripts.ise_monitor
        scripts.ise_monitor.run()
    except:
        print("#### Exception starting scheduled job: ise_monitor")

    launch_dashboard_webhooks(cron)
    launch_pxgrid_monitor(cron)


def launch_dashboard_webhooks(c):
    try:
        import scripts.dashboard_webhook
        scripts.dashboard_webhook.run()
        c.remove_job('dashboard_webhook')
    except:
        print("#### Exception starting scheduled job: dashboard_webhook")
        j = c.get_job('dashboard_webhook')
        if not j:
            c.add_job(launch_dashboard_webhooks, 'interval', minutes=5, id='dashboard_webhook', args=[c])


def launch_pxgrid_monitor(c):
    try:
        loop = asyncio.new_event_loop()
        import scripts.pxgrid_websocket
        th = threading.Thread(target=scripts.pxgrid_websocket.start_background_loop, args=(loop,))
        th.start()
        log = []
        scripts.pxgrid_websocket.sync_pxgrid(loop, log)
        c.remove_job('sync_pxgrid')
    except:
        print("#### Exception starting scheduled job: sync_pxgrid")
        j = c.get_job('sync_pxgrid')
        if not j:
            c.add_job(launch_pxgrid_monitor, 'interval', minutes=5, id='sync_pxgrid', args=[c])
