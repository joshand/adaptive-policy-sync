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

        import scripts.dashboard_monitor
        scripts.dashboard_monitor.run()

        import scripts.dashboard_webhook
        scripts.dashboard_webhook.run()

        import scripts.ise_monitor
        scripts.ise_monitor.run()

        loop = asyncio.new_event_loop()
        import scripts.pxgrid_websocket
        th = threading.Thread(target=scripts.pxgrid_websocket.start_background_loop, args=(loop,))
        th.start()
        log = []
        scripts.pxgrid_websocket.sync_pxgrid(loop, log)
    except:
        print("#### Exception starting scheduled jobs")
