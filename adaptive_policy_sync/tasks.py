import sys
import os
from django_apscheduler.models import DjangoJob

if ('runscript' not in sys.argv) and (os.getenv('SKIPTASKS', '').upper() != "TRUE"):
    import scripts.dashboard_monitor
    import scripts.ise_monitor
    import scripts.clean_tasks
    import scripts.pxgrid_websocket
    import scripts.dashboard_webhook   # noqa: F401
else:
    for j in DjangoJob.objects.all():
        j.delete()
