# import atexit
# from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.schedulers.background import BackgroundScheduler
from django_apscheduler.jobstores import DjangoJobStore
from django_apscheduler.jobstores import register_events

from sync.models import SyncSession, Tag, ACL, Policy
from django.db.models import F, Q
from django.utils.timezone import make_aware
import json
import datetime
import requests
import base64
from scripts.db_trustsec import clean_sgts, clean_sgacls, clean_sgpolicies, merge_sgts, merge_sgacls, merge_sgpolicies
from scripts.dblog import append_log, db_log
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

scheduler = BackgroundScheduler()
scheduler.add_jobstore(DjangoJobStore(), "default")


def ers_get(baseurl, url, un, pw):
    b64 = base64.b64encode((un + ':' + pw).encode()).decode()
    headers = {"Content-Type": "application/json", "Accept": "application/json", "Authorization": "Basic " + b64}
    ret = requests.get(baseurl + "/ers/config" + url, headers=headers, verify=False)
    if ret.ok:
        rj = ret.json()
        if "SearchResult" in rj:
            return rj["SearchResult"]["resources"]
        else:
            return rj
    else:
        return {"error": True, "status_code": ret.status_code, "content": ret.content.decode("utf-8")}


def exec_api_action(method, url, data, headers):
    if data is None or data == "":
        ret = requests.request(method, url, headers=headers, verify=False)
    else:
        ret = requests.request(method, url, data=data, headers=headers, verify=False)
    return ret.content.decode("UTF-8")


def sync_ise_accounts(accounts, log):
    dt = make_aware(datetime.datetime.now())

    for sa in accounts:
        a = sa.iseserver
        append_log(log, "ise_monitor::sync_ise_accounts::Resync -", a.description)
        b64 = base64.b64encode((a.username + ':' + a.password).encode()).decode()
        headers = {"Content-Type": "application/json", "Accept": "application/json", "Authorization": "Basic " + b64}
        sgts = ers_get(a.base_url(), "/sgt", a.username, a.password)
        sgacls = ers_get(a.base_url(), "/sgacl", a.username, a.password)
        sgpolicies = ers_get(a.base_url(), "/egressmatrixcell", a.username, a.password)
        ise = {"sgts": sgts, "sgacls": sgacls, "sgpolicies": sgpolicies}

        if sgts and "error" not in sgts:
            for e in sgts:
                thise = ers_get(a.base_url(), "/sgt/" + str(e["id"]), a.username, a.password)
                merge_sgts("ise", [thise["Sgt"]], sa.ise_source, sa, log)
            clean_sgts("ise", sgts, sa.ise_source, sa, log)

        if sgacls and "error" not in sgacls:
            for e in sgacls:
                thise = ers_get(a.base_url(), "/sgacl/" + str(e["id"]), a.username, a.password)
                merge_sgacls("ise", [thise["Sgacl"]], sa.ise_source, sa, log)
            clean_sgacls("ise", sgacls, sa.ise_source, sa, log)

        if sgpolicies and "error" not in sgpolicies:
            for e in sgpolicies:
                thise = ers_get(a.base_url(), "/egressmatrixcell/" + str(e["id"]), a.username, a.password)
                merge_sgpolicies("ise", [thise["EgressMatrixCell"]], sa.ise_source, sa, log)
            clean_sgpolicies("ise", sgpolicies, sa.ise_source, sa, log)

        a.raw_data = json.dumps(ise)
        a.force_rebuild = False
        a.last_sync = dt
        a.last_update = dt
        a.skip_sync = True
        a.save()

        tags = Tag.objects.filter(syncsession=sa)
        for o in tags:
            if o.do_sync and not o.in_sync() and o.update_dest() == "ise":
                if sa.apply_changes:
                    m, u, d = o.push_config()
                    if m != "":
                        append_log(log, "ise_monitor::sync_ise_accounts::tag API push", o.push_config())
                        ret = exec_api_action(m, u, d, headers)
                        o.last_update_data = ret
                        o.save()
                        sa.iseserver.force_rebuild = True
                        sa.iseserver.save()
                    if o.push_delete:
                        o.delete()
                else:
                    append_log(log, "ise_monitor::sync_ise_accounts::tag needs API push", o.push_config())
        acls = ACL.objects.filter(syncsession=sa)
        for o in acls:
            if not o.in_sync() and o.update_dest() == "ise":
                if sa.apply_changes:
                    m, u, d = o.push_config()
                    if m != "":
                        append_log(log, "ise_monitor::sync_ise_accounts::acl API push", o.push_config())
                        ret = exec_api_action(m, u, d, headers)
                        o.last_update_data = ret
                        o.save()
                        sa.iseserver.force_rebuild = True
                        sa.iseserver.save()
                    if o.push_delete:
                        o.delete()
                else:
                    append_log(log, "ise_monitor::sync_ise_accounts::acl needs API push", o.push_config())
        policies = Policy.objects.filter(syncsession=sa)
        for o in policies:
            if not o.in_sync() and o.update_dest() == "ise":
                if sa.apply_changes:
                    m, u, d = o.push_config()
                    if m != "":
                        append_log(log, "ise_monitor::sync_ise_accounts::policy API push", o.push_config())
                        ret = exec_api_action(m, u, d, headers)
                        o.last_update_data = ret
                        o.save()
                        sa.iseserver.force_rebuild = True
                        sa.iseserver.save()
                    if o.push_delete:
                        o.delete()
                else:
                    append_log(log, "ise_monitor::sync_ise_accounts::policy needs API push", o.push_config())


def sync_ise():
    log = []
    append_log(log, "ise_monitor::sync_ise::Checking ISE Accounts for re-sync...")

    # Ensure that either ISE is source of truth or that Meraki Dashboard has already completed a sync.
    stat = SyncSession.objects.filter(Q(ise_source=True) | Q(dashboard__last_sync__isnull=False))
    if len(stat) <= 0:
        append_log(log, "ise_monitor::sync_ise::Skipping sync as Meraki is primary and hasn't synced.")
    else:
        sync_list = []
        # dbs = ISEServer.objects.filter(force_rebuild=True)
        dbs = SyncSession.objects.filter(Q(iseserver__force_rebuild=True) | Q(force_rebuild=True))
        for db in dbs:
            append_log(log, "ise_monitor::sync_ise::Force Rebuild -", db)
            # sync_ise_accounts(dbs.iseserver)
            sync_list.append(db)

        # dbs = ISEServer.objects.all().exclude(last_sync=F('last_update'))
        dbs = SyncSession.objects.all().exclude(iseserver__last_sync=F('iseserver__last_update'))
        for db in dbs:
            if db not in sync_list:
                append_log(log, "ise_monitor::sync_ise::Out of Sync -", db)
                # sync_dashboard_accounts(dbs)
                sync_list.append(db)

        ss = SyncSession.objects.all()
        for s in ss:
            ctime = make_aware(datetime.datetime.now()) - datetime.timedelta(seconds=s.sync_interval)
            dbs = SyncSession.objects.filter(iseserver__last_sync__lte=ctime)
            for db in dbs:
                if db not in sync_list:
                    append_log(log, "ise_monitor::sync_ise::Past sync interval -", dbs)
                    sync_list.append(db)
                    # sync_dashboard_accounts(dbs)

        for s in sync_list:
            if not s.sync_enabled:
                append_log(log, "ise_monitor::sync_ise::Sync Disabled -", s)
                sync_list.remove(s)

        sync_ise_accounts(sync_list, log)

    append_log(log, "ise_monitor::sync_ise::Done")
    db_log("ise_monitor", log)


def run():
    pass
    # # Enable the job scheduler to run schedule jobs
    # cron = BackgroundScheduler()
    #
    # # Explicitly kick off the background thread
    # cron.start()
    # cron.remove_all_jobs()
    # cron.add_job(sync_ise)
    # cron.add_job(sync_ise, 'interval', seconds=10)
    #
    # # Shutdown your cron thread if the web process is stopped
    # atexit.register(lambda: cron.shutdown(wait=False))


@scheduler.scheduled_job("interval", seconds=10, id="ise_monitor")
def job():
    sync_ise()


register_events(scheduler)
scheduler.start()
