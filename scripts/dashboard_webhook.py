from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from sync.models import Dashboard
from pyngrok import ngrok
import json
import sys
import meraki
from scripts.dblog import append_log, db_log


def run():
    log = []
    dbs = Dashboard.objects.filter(webhook_enable=True)
    if dbs and len(dbs) > 0:
        db = dbs[0]
        dashboard = meraki.DashboardAPI(api_key=db.apikey, print_console=False, output_log=False)
        if db.webhook_ngrok:
            try:
                public_url = ngrok.connect(sys.argv[-1], "http")
            except Exception:
                public_url = ngrok.connect(8000, "http")

            db.webhook_url = public_url.replace("http://", "https://") + "/webhook/"
            db.save()

        nets = dashboard.networks.getOrganizationNetworks(db.orgid)
        for n in nets:
            whid = None
            whurl = dashboard.http_servers.getNetworkHttpServers(networkId=n["id"])
            if len(whurl) <= 0:
                append_log(log, "creating new webhook for network", n["id"])
                wh = dashboard.http_servers.createNetworkHttpServer(networkId=n["id"], name="adaptive-policy-sync",
                                                                    url=db.webhook_url)
                whid = wh["id"]
            else:
                for w in whurl:
                    if w["name"] == "adaptive-policy-sync":
                        append_log(log, "updating for network", n["id"])
                        dashboard.http_servers.updateNetworkHttpServer(networkId=n["id"], id=w["id"],
                                                                       url=db.webhook_url)
                        whid = w["id"]

            if whid:
                al = dashboard.alert_settings.getNetworkAlertSettings(networkId=n["id"])
                for a in al["alerts"]:
                    if a["type"] == "settingsChanged":
                        a["alertDestinations"]["httpServerIds"].append(whid)
                        a["enabled"] = True

                append_log(log, "updating alert settings", al)
                r = dashboard.alert_settings.updateNetworkAlertSettings(networkId=n["id"],
                                                                        defaultDestinations=al["defaultDestinations"],
                                                                        alerts=al["alerts"])
                append_log(log, "update response", r)
    else:
        raise Exception("Dashboard webhooks are not configured")

    db_log("dashboard_webhook", log)


@csrf_exempt
def process_webhook(request):
    log = []
    if request.method == 'POST':
        whdata = json.loads(request.body)
        append_log(log, "webhook post", whdata)

        dbs = Dashboard.objects.filter(webhook_enable=True)
        if len(dbs) > 0:
            db = dbs[0]
            db.force_rebuild = True
            db.save()
            append_log(log, "setting dashboard to force rebuild")

        db_log("dashboard_webhook", log)

    return HttpResponse("Send webhooks here as POST requests.")
