import sys
import os
if 'runscript' not in sys.argv and os.getenv('SKIPTASKS', '').upper() != "TRUE":
    import scripts.dashboard_monitor
    import scripts.ise_monitor
    import scripts.clean_tasks
    import scripts.pxgrid_websocket
    import scripts.dashboard_webhook   # noqa: F401
