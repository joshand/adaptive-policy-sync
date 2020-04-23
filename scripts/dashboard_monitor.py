import atexit
from apscheduler.schedulers.background import BackgroundScheduler
from sync.models import SyncSession, Tag, ACL, Policy
from django.db.models import F, Q
from django.utils.timezone import make_aware
import meraki
import requests
import datetime
import json
from scripts.db_trustsec import clean_sgts, clean_sgacls, clean_sgpolicies, merge_sgts, merge_sgacls, merge_sgpolicies
from scripts.dblog import append_log, db_log


def meraki_read_sgt(baseurl, orgid, headers):
    ret = requests.get(baseurl + "/organizations/" + str(orgid) + "/adaptivePolicy/groups", headers=headers)
    return ret.json()


def meraki_read_sgacl(baseurl, orgid, headers):
    ret = requests.get(baseurl + "/organizations/" + str(orgid) + "/adaptivePolicy/acls", headers=headers)
    return ret.json()


def meraki_read_sgpolicy(baseurl, orgid, headers):
    ret = requests.get(baseurl + "/organizations/" + str(orgid) + "/adaptivePolicy/bindings", headers=headers)
    j = ret.json()
    outlist = []
    for e in j:
        newe = e
        newe["bindingId"] = "s" + str(e["srcGroupId"]) + "-" + "d" + str(e["dstGroupId"])
        outlist.append(newe)
    return outlist


def exec_api_action(method, url, data, headers):
    if data is None or data == "":
        ret = requests.request(method, url, headers=headers)
    else:
        ret = requests.request(method, url, data=data, headers=headers)
    return ret.content.decode("UTF-8")


def sync_dashboard_accounts(accounts, log):
    dt = make_aware(datetime.datetime.now())

    for sa in accounts:
        a = sa.dashboardmerge_sgpolicies
        append_log(log, "dashboard_monitor::sync_dashboard_accounts::Resync -", a.description)
        headers = {"X-Cisco-Meraki-API-Key": a.apikey, "Content-Type": "application/json"}
        nets = meraki.getnetworklist(a.apikey, a.orgid, suppressprint=True)
        sgts = meraki_read_sgt(a.baseurl, a.orgid, headers)
        sgacls = meraki_read_sgacl(a.baseurl, a.orgid, headers)
        sgpolicies = meraki_read_sgpolicy(a.baseurl, a.orgid, headers)

        merge_sgts("meraki", sgts, not sa.ise_source, sa, log)
        merge_sgacls("meraki", sgacls, not sa.ise_source, sa, log)
        merge_sgpolicies("meraki", sgpolicies, not sa.ise_source, sa, log)
        clean_sgts("meraki", sgts, not sa.ise_source, sa, log)
        clean_sgacls("meraki", sgacls, not sa.ise_source, sa, log)
        clean_sgpolicies("meraki", sgpolicies, not sa.ise_source, sa, log)

        a.raw_data = json.dumps(nets)
        a.force_rebuild = False
        a.last_sync = dt
        a.last_update = dt
        a.skip_sync = True
        a.save()

        tags = Tag.objects.filter(syncsession=sa)
        for o in tags:
            if o.do_sync and not o.in_sync() and o.update_dest() == "meraki":
                if sa.apply_changes:
                    m, u, d = o.push_config()
                    if m != "":
                        append_log(log, "dashboard_monitor::sync_dashboard_accounts::tag API push", o.push_config())
                        ret = exec_api_action(m, u, d, headers)
                        o.last_update_data = ret
                        o.save()
                        sa.dashboard.force_rebuild = True
                        sa.dashboard.save()
                    if o.push_delete:
                        o.delete()
                else:
                    append_log(log, "dashboard_monitor::sync_dashboard_accounts::tag needs API push", o.push_config())
            elif not o.do_sync and o.push_delete:
                o.delete()
        acls = ACL.objects.filter(syncsession=sa)
        for o in acls:
            if not o.in_sync() and o.update_dest() == "meraki":
                if sa.apply_changes:
                    m, u, d = o.push_config()
                    if m != "":
                        append_log(log, "dashboard_monitor::sync_dashboard_accounts::acl API push", o.push_config())
                        ret = exec_api_action(m, u, d, headers)
                        o.last_update_data = ret
                        o.save()
                        sa.dashboard.force_rebuild = True
                        sa.dashboard.save()
                    if o.push_delete:
                        o.delete()
                else:
                    append_log(log, "dashboard_monitor::sync_dashboard_accounts::acl needs API push", o.push_config())
            elif o.push_delete:
                o.delete()
        policies = Policy.objects.filter(syncsession=sa)
        for o in policies:
            if not o.in_sync() and o.update_dest() == "meraki":
                if sa.apply_changes:
                    m, u, d = o.push_config()
                    if m != "":
                        append_log(log, "dashboard_monitor::sync_dashboard_accounts::policy API push", o.push_config())
                        ret = exec_api_action(m, u, d, headers)
                        o.last_update_data = ret
                        o.save()
                        sa.dashboard.force_rebuild = True
                        sa.dashboard.save()
                    if o.push_delete:
                        o.delete()
                else:
                    append_log(log, "dashboard_monitor::sync_dashboard_accounts::policy needs API push",
                               o.push_config())
            elif o.push_delete:
                o.delete()


def sync_dashboard():
    log = []
    append_log(log, "dashboard_monitor::sync_dashboard::Checking Dashboard Accounts for re-sync...")
    sync_list = []
    # dbs = Dashboard.objects.filter(force_rebuild=True)
    dbs = SyncSession.objects.filter(Q(dashboard__force_rebuild=True) | Q(force_rebuild=True))
    for db in dbs:
        append_log(log, "dashboard_monitor::sync_dashboard::Force Rebuild -", db)
        # sync_dashboard_accounts(dbs)
        db.force_rebuild = False
        db.save()
        sync_list.append(db)

    # dbs = Dashboard.objects.all().exclude(last_sync=F('last_update'))
    dbs = SyncSession.objects.all().exclude(dashboard__last_sync=F('dashboard__last_update'))
    for db in dbs:
        if db not in sync_list:
            append_log(log, "dashboard_monitor::sync_dashboard::Out of Sync -", db)
            # sync_dashboard_accounts(dbs)
            sync_list.append(db)

    ss = SyncSession.objects.all()
    for s in ss:
        ctime = make_aware(datetime.datetime.now()) - datetime.timedelta(seconds=s.sync_interval)
        dbs = SyncSession.objects.filter(dashboard__last_sync__lte=ctime)
        for db in dbs:
            if db not in sync_list:
                append_log(log, "dashboard_monitor::sync_dashboard::Past sync interval -", dbs)
                sync_list.append(db)
                # sync_dashboard_accounts(dbs)

    for s in sync_list:
        if not s.sync_enabled:
            sync_list.remove(s)

    sync_dashboard_accounts(sync_list, log)
    append_log(log, "dashboard_monitor::sync_dashboard::Done")
    db_log("dashboard_monitor", log)


def run():
    # Enable the job scheduler to run schedule jobs
    cron = BackgroundScheduler()

    # Explicitly kick off the background thread
    cron.start()
    cron.remove_all_jobs()
    cron.add_job(sync_dashboard)
    cron.add_job(sync_dashboard, 'interval', seconds=10)

    # Shutdown your cron thread if the web process is stopped
    atexit.register(lambda: cron.shutdown(wait=False))
