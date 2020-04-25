# import atexit
# from apscheduler.schedulers.background import BackgroundScheduler
# import threading
# import asyncio
import sys
# import os
if 'runscript' not in sys.argv:
    try:
        import scripts.dashboard_monitor
        import scripts.ise_monitor
        import scripts.clean_tasks
        import scripts.pxgrid_websocket
        import scripts.dashboard_webhook
    except Exception:
        print("# Exception loading background tasks")


def run_tasks():
    if 'runscript' not in sys.argv:
        scripts.dashboard_webhook.run()

# def old_run_tasks():
#     skiptasks = os.getenv('SKIPTASKS')
#     if skiptasks and skiptasks.upper() == "TRUE":
#         print("Skipping tasks because 'SKIPTASKS' environment variable set.")
#         return None
#     # Enable the job scheduler to run schedule jobs
#     cron = BackgroundScheduler()
#
#     # Explicitly kick off the background thread
#     cron.start()
#     cron.remove_all_jobs()
#     # Shutdown your cron thread if the web process is stopped
#     atexit.register(lambda: cron.shutdown(wait=False))
#
#     if 'runserver' not in sys.argv:
#         return None
#     try:
#         import scripts.clean_tasks
#         scripts.clean_tasks.run()
#     except Exception as e:
#         print("#### Exception starting scheduled job: clean_tasks", e)
#
#     try:
#         import scripts.dashboard_monitor
#         scripts.dashboard_monitor.run()
#     except Exception as e:
#         print("#### Exception starting scheduled job: dashboard_monitor", e)
#
#     try:
#         import scripts.ise_monitor
#         scripts.ise_monitor.run()
#     except Exception as e:
#         print("#### Exception starting scheduled job: ise_monitor", e)
#
#     launch_dashboard_webhooks(cron)
#     launch_pxgrid_monitor(cron)
#
#
# def launch_dashboard_webhooks(c):
#     try:
#         import scripts.dashboard_webhook
#         scripts.dashboard_webhook.run()
#         j = c.get_job('dashboard_webhook')
#         if j:
#             c.remove_job('dashboard_webhook')
#     except Exception as e:
#         print("#### Exception starting scheduled job: dashboard_webhook", e)
#         j = c.get_job('dashboard_webhook')
#         if not j:
#             c.add_job(launch_dashboard_webhooks, 'interval', minutes=5, id='dashboard_webhook', args=[c])
#
#
# def launch_pxgrid_monitor(c):
#     try:
#         loop = asyncio.new_event_loop()
#         import scripts.pxgrid_websocket
#         th = threading.Thread(target=scripts.pxgrid_websocket.start_background_loop, args=(loop,))
#         th.start()
#         log = []
#         scripts.pxgrid_websocket.sync_pxgrid(loop, log)
#         j = c.get_job('sync_pxgrid')
#         if j:
#             c.remove_job('sync_pxgrid')
#     except Exception as e:
#         print("#### Exception starting scheduled job: sync_pxgrid", e)
#         j = c.get_job('sync_pxgrid')
#         if not j:
#             c.add_job(launch_pxgrid_monitor, 'interval', minutes=5, id='sync_pxgrid', args=[c])
