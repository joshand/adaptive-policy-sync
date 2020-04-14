import threading
import asyncio
import sys
from sync.models import *


def run_tasks():
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
        import scripts.dashboard_webhook
        scripts.dashboard_webhook.run()
    except:
        print("#### Exception starting scheduled job: dashboard_webhook")

    try:
        import scripts.ise_monitor
        scripts.ise_monitor.run()
    except:
        print("#### Exception starting scheduled job: ise_monitor")

    try:
        loop = asyncio.new_event_loop()
        import scripts.pxgrid_websocket
        th = threading.Thread(target=scripts.pxgrid_websocket.start_background_loop, args=(loop,))
        th.start()
        log = []
        scripts.pxgrid_websocket.sync_pxgrid(loop, log)
    except:
        print("#### Exception starting scheduled job: sync_pxgrid")
