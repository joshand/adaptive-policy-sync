import pytest
from django.core import serializers
from django.forms.models import model_to_dict
from django.test import TestCase
from .models import Upload, UploadZip, ISEServer, Dashboard, SyncSession, Tag, ACL, Policy, Task
from sync._config import *
import meraki
from ise import ERS
from scripts.meraki_addons import meraki_read_sgt, meraki_read_sgacl, meraki_read_sgpolicy, meraki_update_sgt, \
    meraki_create_sgt, meraki_update_sgacl, meraki_create_sgacl, meraki_update_sgpolicy, meraki_delete_sgt, \
    meraki_delete_sgacl
from django.conf import settings
import scripts.dashboard_monitor
import scripts.ise_monitor


def reset_dashboard(db):
    dashboard = meraki.DashboardAPI(base_url=db.baseurl, api_key=db.apikey, print_console=False, output_log=False,
                                    caller=settings.CUSTOM_UA)
    sgts = meraki_read_sgt(dashboard, db.orgid)
    sgacls = meraki_read_sgacl(dashboard, db.orgid)
    sgpolicies = meraki_read_sgpolicy(dashboard, db.orgid)
    for s in sgts:
        if not s["value"] in whitelisted_sgts:
            print("Removing SGT", s["value"], "from Meraki Dashboard...")
            meraki_delete_sgt(dashboard, db.orgid, s["groupId"])

    for s in sgacls:
        print("Removing SGACL", s["name"], "from Meraki Dashboard...")
        meraki_delete_sgacl(dashboard, db.orgid, s["aclId"])

    # for s in sgpolicies:
    #     print("Removing Egress Policy", s["name"], "from Meraki Dashboard...")
    #     # We technically shouldn't need to remove policies; they will clear from dashboard when the groups are deleted;
    #     #  If the group did get deleted successfully, this will error out, hence the try block
    #     meraki_update_sgpolicy(dashboard, db.orgid, srcGroupId=s["srcGroupId"], dstGroupId=s["dstGroupId"],
    #                            aclIds=None, catchAllRule="global", name="")


def reset_ise(db):
    ise = ERS(ise_node=db.ipaddress, ers_user=db.username, ers_pass=db.password, verify=False, disable_warnings=True)
    default_sgts = [d['value'] for d in ise_default_sgts]
    default_sgacls = [d['name'] for d in ise_default_sgacls]
    default_policies = [d['name'] for d in ise_default_policies]

    sgts = ise.get_sgts(detail=True)
    sgacls = ise.get_sgacls(detail=True)
    sgpolicies = ise.get_egressmatrixcells(detail=True)

    for s in sgts["response"]:
        if not s["value"] in (whitelisted_sgts + default_sgts):
            print("Removing SGT", s["value"], "from Cisco ISE...")
            ise.delete_sgt(s["id"])

    for s in sgacls["response"]:
        if not s["name"] in (whitelisted_sgacls + default_sgacls):
            print("Removing SGACL", s["name"], "from Cisco ISE...")
            ise.delete_sgacl(s["id"])

    for s in sgpolicies["response"]:
        if not s["name"] in (whitelisted_policies + default_policies):
            print("Removing Egress Policy", s["name"], "from Cisco ISE...")
            ise.delete_egressmatrixcell(s["id"])

    current_vals = [d['value'] for d in sgts["response"]]
    for s in ise_default_sgts:
        if not s["value"] in current_vals:
            print("Adding SGT", s["value"], "to Cisco ISE...")
            ise.add_sgt(s["name"], s["description"], s["value"])

    current_vals = [d['name'] for d in sgacls["response"]]
    for s in ise_default_sgacls:
        if not s["name"] in current_vals:
            print("Adding SGACL", s["name"], "to Cisco ISE...")
            ise.add_sgacl(s["name"], s["description"], s["version"], s["aclcontent"])

    current_vals = [d['name'] for d in sgpolicies["response"]]
    for s in ise_default_policies:
        if not s["name"] in current_vals:
            print("Adding Egress Policy", s["name"], "to Cisco ISE...")
            r = ise.add_egressmatrixcell(s["src"], s["dst"], s["default"], acls=s["acls"], description=s["description"])


@pytest.fixture(params=[0])
def arg(request):
    return request.getfixturevalue(request.param)


@pytest.fixture
@pytest.mark.django_db
def setup_ise24_i_src():
    cm = Dashboard.objects.create(description="Meraki", apikey=merakiapi["apikey"], orgid=merakiapi["orgid"],
                                  baseurl="https://api.meraki.com/api/v1")
    reset_dashboard(cm)

    ISEServer.objects.all().delete()
    s = servers["2.4"]
    # UploadZip.objects.create(description="unittest", file=s["cert"])
    # u = Upload.objects.all()
    # print(u)

    ci = ISEServer.objects.create(description=s["desc"], ipaddress=s["ip"], username=s["user"],
                                  password=s["pass"])
    reset_ise(ci)
    ss = SyncSession.objects.create(description="Sync", dashboard=cm, iseserver=ci, force_rebuild=True,
                                    ise_source=True)


@pytest.fixture
@pytest.mark.django_db
def setup_ise26_i_src():
    cm = Dashboard.objects.create(description="Meraki", apikey=merakiapi["apikey"], orgid=merakiapi["orgid"],
                                  baseurl="https://api.meraki.com/api/v1")
    reset_dashboard(cm)

    ISEServer.objects.all().delete()
    s = servers["2.6"]
    # UploadZip.objects.create(description="unittest", file=s["cert"])
    # u = Upload.objects.all()
    # print(u)

    ci = ISEServer.objects.create(description=s["desc"], ipaddress=s["ip"], username=s["user"],
                                  password=s["pass"])
    reset_ise(ci)
    ss = SyncSession.objects.create(description="Sync", dashboard=cm, iseserver=ci, force_rebuild=True,
                                    ise_source=True)


@pytest.fixture
@pytest.mark.django_db
def setup_ise27_i_src():
    cm = Dashboard.objects.create(description="Meraki", apikey=merakiapi["apikey"], orgid=merakiapi["orgid"],
                                  baseurl="https://api.meraki.com/api/v1")
    reset_dashboard(cm)

    ISEServer.objects.all().delete()
    s = servers["2.7"]
    # UploadZip.objects.create(description="unittest", file=s["cert"])
    # u = Upload.objects.all()
    # print(u)

    ci = ISEServer.objects.create(description=s["desc"], ipaddress=s["ip"], username=s["user"],
                                  password=s["pass"])
    reset_ise(ci)
    ss = SyncSession.objects.create(description="Sync", dashboard=cm, iseserver=ci, force_rebuild=True,
                                    ise_source=True)


@pytest.fixture
@pytest.mark.django_db
def setup_ise30_i_src():
    cm = Dashboard.objects.create(description="Meraki", apikey=merakiapi["apikey"], orgid=merakiapi["orgid"],
                                  baseurl="https://api.meraki.com/api/v1")
    reset_dashboard(cm)

    ISEServer.objects.all().delete()
    s = servers["3.0"]
    # UploadZip.objects.create(description="unittest", file=s["cert"])
    # u = Upload.objects.all()
    # print(u)

    ci = ISEServer.objects.create(description=s["desc"], ipaddress=s["ip"], username=s["user"],
                                  password=s["pass"])
    reset_ise(ci)
    ss = SyncSession.objects.create(description="Sync", dashboard=cm, iseserver=ci, force_rebuild=True,
                                    ise_source=True)


@pytest.fixture
@pytest.mark.django_db
def setup_ise24_m_src():
    cm = Dashboard.objects.create(description="Meraki", apikey=merakiapi["apikey"], orgid=merakiapi["orgid"],
                                  baseurl="https://api.meraki.com/api/v1")
    reset_dashboard(cm)

    ISEServer.objects.all().delete()
    s = servers["2.4"]
    # UploadZip.objects.create(description="unittest", file=s["cert"])
    # u = Upload.objects.all()
    # print(u)

    ci = ISEServer.objects.create(description=s["desc"], ipaddress=s["ip"], username=s["user"],
                                  password=s["pass"])
    reset_ise(ci)
    ss = SyncSession.objects.create(description="Sync", dashboard=cm, iseserver=ci, force_rebuild=True,
                                    ise_source=False)


@pytest.fixture
@pytest.mark.django_db
def setup_ise26_m_src():
    cm = Dashboard.objects.create(description="Meraki", apikey=merakiapi["apikey"], orgid=merakiapi["orgid"],
                                  baseurl="https://api.meraki.com/api/v1")
    reset_dashboard(cm)

    ISEServer.objects.all().delete()
    s = servers["2.6"]
    # UploadZip.objects.create(description="unittest", file=s["cert"])
    # u = Upload.objects.all()
    # print(u)

    ci = ISEServer.objects.create(description=s["desc"], ipaddress=s["ip"], username=s["user"],
                                  password=s["pass"])
    reset_ise(ci)
    ss = SyncSession.objects.create(description="Sync", dashboard=cm, iseserver=ci, force_rebuild=True,
                                    ise_source=False)


@pytest.fixture
@pytest.mark.django_db
def setup_ise27_m_src():
    cm = Dashboard.objects.create(description="Meraki", apikey=merakiapi["apikey"], orgid=merakiapi["orgid"],
                                  baseurl="https://api.meraki.com/api/v1")
    reset_dashboard(cm)

    ISEServer.objects.all().delete()
    s = servers["2.7"]
    # UploadZip.objects.create(description="unittest", file=s["cert"])
    # u = Upload.objects.all()
    # print(u)

    ci = ISEServer.objects.create(description=s["desc"], ipaddress=s["ip"], username=s["user"],
                                  password=s["pass"])
    reset_ise(ci)
    ss = SyncSession.objects.create(description="Sync", dashboard=cm, iseserver=ci, force_rebuild=True,
                                    ise_source=False)


@pytest.fixture
@pytest.mark.django_db
def setup_ise30_m_src():
    cm = Dashboard.objects.create(description="Meraki", apikey=merakiapi["apikey"], orgid=merakiapi["orgid"],
                                  baseurl="https://api.meraki.com/api/v1")
    reset_dashboard(cm)

    ISEServer.objects.all().delete()
    s = servers["3.0"]
    # UploadZip.objects.create(description="unittest", file=s["cert"])
    # u = Upload.objects.all()
    # print(u)

    ci = ISEServer.objects.create(description=s["desc"], ipaddress=s["ip"], username=s["user"],
                                  password=s["pass"])
    reset_ise(ci)
    ss = SyncSession.objects.create(description="Sync", dashboard=cm, iseserver=ci, force_rebuild=True,
                                    ise_source=False)


@pytest.fixture
@pytest.mark.django_db
def setup_ise24_data_i_src(setup_ise24_i_src):
    scripts.ise_monitor.sync_ise()
    scripts.dashboard_monitor.sync_dashboard()


@pytest.fixture
@pytest.mark.django_db
def setup_ise26_data_i_src(setup_ise26_i_src):
    scripts.ise_monitor.sync_ise()
    scripts.dashboard_monitor.sync_dashboard()


@pytest.fixture
@pytest.mark.django_db
def setup_ise27_data_i_src(setup_ise27_i_src):
    scripts.ise_monitor.sync_ise()
    scripts.dashboard_monitor.sync_dashboard()


@pytest.fixture
@pytest.mark.django_db
def setup_ise30_data_i_src(setup_ise30_i_src):
    scripts.ise_monitor.sync_ise()
    scripts.dashboard_monitor.sync_dashboard()


@pytest.fixture
@pytest.mark.django_db
def setup_ise24_data_m_src(setup_ise24_m_src):
    scripts.dashboard_monitor.sync_dashboard()
    scripts.ise_monitor.sync_ise()


@pytest.fixture
@pytest.mark.django_db
def setup_ise26_data_m_src(setup_ise26_m_src):
    scripts.dashboard_monitor.sync_dashboard()
    scripts.ise_monitor.sync_ise()


@pytest.fixture
@pytest.mark.django_db
def setup_ise27_data_m_src(setup_ise27_m_src):
    scripts.dashboard_monitor.sync_dashboard()
    scripts.ise_monitor.sync_ise()


@pytest.fixture
@pytest.mark.django_db
def setup_ise30_data_m_src(setup_ise30_m_src):
    scripts.dashboard_monitor.sync_dashboard()
    scripts.ise_monitor.sync_ise()


@pytest.fixture
@pytest.mark.django_db
def setup_ise24_data_sync_i_src(setup_ise24_data_i_src):
    sgts = Tag.objects.order_by("tag_number")
    for s in sgts:
        if s.tag_number in sync_tags:
            s.do_sync = True
            s.save()
    scripts.ise_monitor.sync_ise()
    scripts.dashboard_monitor.sync_dashboard()


@pytest.fixture
@pytest.mark.django_db
def setup_ise26_data_sync_i_src(setup_ise26_data_i_src):
    sgts = Tag.objects.order_by("tag_number")
    for s in sgts:
        if s.tag_number in sync_tags:
            s.do_sync = True
            s.save()
    scripts.ise_monitor.sync_ise()
    scripts.dashboard_monitor.sync_dashboard()


@pytest.fixture
@pytest.mark.django_db
def setup_ise27_data_sync_i_src(setup_ise27_data_i_src):
    sgts = Tag.objects.order_by("tag_number")
    for s in sgts:
        if s.tag_number in sync_tags:
            s.do_sync = True
            s.save()
    scripts.ise_monitor.sync_ise()
    scripts.dashboard_monitor.sync_dashboard()


@pytest.fixture
@pytest.mark.django_db
def setup_ise30_data_sync_i_src(setup_ise30_data_i_src):
    sgts = Tag.objects.order_by("tag_number")
    for s in sgts:
        if s.tag_number in sync_tags:
            s.do_sync = True
            s.save()
    scripts.ise_monitor.sync_ise()
    scripts.dashboard_monitor.sync_dashboard()


@pytest.fixture
@pytest.mark.django_db
def setup_ise24_data_sync_m_src(setup_ise24_data_m_src):
    sgts = Tag.objects.order_by("tag_number")
    for s in sgts:
        if s.tag_number in sync_tags:
            s.do_sync = True
            s.save()
    scripts.dashboard_monitor.sync_dashboard()
    scripts.ise_monitor.sync_ise()


@pytest.fixture
@pytest.mark.django_db
def setup_ise26_data_sync_m_src(setup_ise26_data_m_src):
    sgts = Tag.objects.order_by("tag_number")
    for s in sgts:
        if s.tag_number in sync_tags:
            s.do_sync = True
            s.save()
    scripts.dashboard_monitor.sync_dashboard()
    scripts.ise_monitor.sync_ise()


@pytest.fixture
@pytest.mark.django_db
def setup_ise27_data_sync_m_src(setup_ise27_data_m_src):
    sgts = Tag.objects.order_by("tag_number")
    for s in sgts:
        if s.tag_number in sync_tags:
            s.do_sync = True
            s.save()
    scripts.dashboard_monitor.sync_dashboard()
    scripts.ise_monitor.sync_ise()


@pytest.fixture
@pytest.mark.django_db
def setup_ise30_data_sync_m_src(setup_ise30_data_m_src):
    sgts = Tag.objects.order_by("tag_number")
    for s in sgts:
        if s.tag_number in sync_tags:
            s.do_sync = True
            s.save()
    scripts.dashboard_monitor.sync_dashboard()
    scripts.ise_monitor.sync_ise()


@pytest.mark.parametrize('arg', ['setup_ise24_i_src', 'setup_ise26_i_src', 'setup_ise27_i_src', 'setup_ise30_i_src'],
                         indirect=True)
@pytest.mark.django_db
def test_ise_dashboard_unable_to_sync_first(arg):
    """With ISE set to Authoritative Source, Dashboard should be unable to sync first"""
    msg, log = scripts.dashboard_monitor.sync_dashboard()
    print(msg)
    assert msg == "SYNC_DASHBOARD-ISE_NEEDS_SYNC"


@pytest.mark.parametrize('arg', ['setup_ise24_i_src', 'setup_ise26_i_src', 'setup_ise27_i_src', 'setup_ise30_i_src'],
                         indirect=True)
@pytest.mark.django_db
def test_ise_iseserver_can_sync(arg):
    """With ISE set to Authoritative Source, ISE should be able to sync first"""
    msg, log = scripts.ise_monitor.sync_ise()
    print(msg)
    assert (msg == "SYNC_ISE-ISE_FORCE_REBUILD") or (msg == "SYNC_ISE-CONFIG_SYNC_TIMESTAMP_MISMATCH")


@pytest.mark.parametrize('arg', ['setup_ise24_i_src', 'setup_ise26_i_src', 'setup_ise27_i_src', 'setup_ise30_i_src'],
                         indirect=True)
@pytest.mark.django_db
def test_ise_dashboard_can_sync_next(arg):
    """With ISE set to Authoritative Source, Dashboard should be able to sync after ISE"""
    msg, log = scripts.ise_monitor.sync_ise()
    msg, log = scripts.dashboard_monitor.sync_dashboard()
    print(msg)
    assert (msg == "SYNC_DASHBOARD-DASHBOARD_FORCE_REBUILD") or (msg == "SYNC_DASHBOARD-CONFIG_SYNC_TIMESTAMP_MISMATCH")


@pytest.mark.parametrize('arg', ['setup_ise24_m_src', 'setup_ise26_m_src', 'setup_ise27_m_src', 'setup_ise30_m_src'],
                         indirect=True)
@pytest.mark.django_db
def test_dashboard_ise_unable_to_sync_first(arg):
    """With Meraki Dashboard set to Authoritative Source, ISE should be unable to sync first"""
    msg, log = scripts.ise_monitor.sync_ise()
    print(msg)
    assert msg == "SYNC_ISE-DASHBOARD_NEEDS_SYNC"


@pytest.mark.parametrize('arg', ['setup_ise24_m_src', 'setup_ise26_m_src', 'setup_ise27_m_src', 'setup_ise30_m_src'],
                         indirect=True)
@pytest.mark.django_db
def test_dashboard_can_sync(arg):
    """With Meraki Dashboard set to Authoritative Source, Dashboard should be able to sync first"""
    msg, log = scripts.dashboard_monitor.sync_dashboard()
    print(msg)
    assert (msg == "SYNC_DASHBOARD-DASHBOARD_FORCE_REBUILD") or (msg == "SYNC_DASHBOARD-CONFIG_SYNC_TIMESTAMP_MISMATCH")


@pytest.mark.parametrize('arg', ['setup_ise24_m_src', 'setup_ise26_m_src', 'setup_ise27_m_src', 'setup_ise30_m_src'],
                         indirect=True)
@pytest.mark.django_db
def test_dashboard_ise_can_sync_next(arg):
    """With Meraki Dashboard set to Authoritative Source, ISE should be able to sync after Dashboard"""
    msg, log = scripts.dashboard_monitor.sync_dashboard()
    msg, log = scripts.ise_monitor.sync_ise()
    print(msg)
    assert (msg == "SYNC_ISE-ISE_FORCE_REBUILD") or (msg == "SYNC_ISE-CONFIG_SYNC_TIMESTAMP_MISMATCH")


@pytest.mark.parametrize('arg', ['setup_ise24_data_i_src', 'setup_ise26_data_i_src', 'setup_ise27_data_i_src',
                                 'setup_ise30_data_i_src', 'setup_ise24_data_m_src', 'setup_ise26_data_m_src',
                                 'setup_ise27_data_m_src', 'setup_ise30_data_m_src'], indirect=True)
@pytest.mark.django_db
def test_ise_sgts_in_database(arg):
    """Whitelisted SGTs must have Dashboard and ISE IDs in the DB; Default SGTs must have ISE IDs in the DB"""
    success = True
    default_vals = [d['value'] for d in ise_default_sgts]

    sgts = Tag.objects.order_by("tag_number")
    for s in sgts:
        if s.tag_number in whitelisted_sgts:
            if s.meraki_id is None or s.meraki_id == "" or s.ise_id is None or s.ise_id is None:
                success = False
                print("1 (FAIL) :", model_to_dict(s))
            else:
                print("1 (SUCCESS) :", model_to_dict(s))
        if s.tag_number in default_vals:
            if s.ise_id is None or s.ise_id is None:
                success = False
                print("2 (FAIL) :", model_to_dict(s))
            else:
                print("2 (SUCCESS) :", model_to_dict(s))

    if len(sgts) != len(whitelisted_sgts + ise_default_sgts):
        success = False
        print("3 (FAIL) : ", sgts, (whitelisted_sgts + ise_default_sgts))
    else:
        print("3 (SUCCESS) : ", sgts, (whitelisted_sgts + ise_default_sgts))

    assert success


@pytest.mark.parametrize('arg', ['setup_ise24_data_i_src', 'setup_ise26_data_i_src', 'setup_ise27_data_i_src',
                                 'setup_ise30_data_i_src', 'setup_ise24_data_m_src', 'setup_ise26_data_m_src',
                                 'setup_ise27_data_m_src', 'setup_ise30_data_m_src'], indirect=True)
@pytest.mark.django_db
def test_ise_sgacls_in_database(arg):
    """Whitelisted SGACLs must have ISE IDs in the DB and be invisible; Default SGACLs must have ISE IDs in the DB"""
    success = True
    default_vals = [d['name'] for d in ise_default_sgacls]

    sgacls = ACL.objects.order_by("name")
    for s in sgacls:
        if s.name in whitelisted_sgacls:
            if s.ise_id is None or s.ise_id is None:
                success = False
                print("1 (FAIL-MISSING) :", model_to_dict(s))
            elif s.visible:
                success = False
                print("1 (FAIL-VISIBLE) :", model_to_dict(s))
            else:
                print("1 (SUCCESS) :", model_to_dict(s))
        if s.name in default_vals:
            if s.ise_id is None or s.ise_id is None:
                success = False
                print("2 (FAIL) :", model_to_dict(s))
            else:
                print("2 (SUCCESS) :", model_to_dict(s))

    if len(sgacls) != len(whitelisted_sgacls + ise_default_sgacls):
        success = False
        print("3 (FAIL) : ", sgacls, (whitelisted_sgacls + ise_default_sgacls))
    else:
        print("3 (SUCCESS) : ", sgacls, (whitelisted_sgacls + ise_default_sgacls))

    assert success


@pytest.mark.parametrize('arg', ['setup_ise24_data_i_src', 'setup_ise26_data_i_src', 'setup_ise27_data_i_src',
                                 'setup_ise30_data_i_src', 'setup_ise24_data_m_src', 'setup_ise26_data_m_src',
                                 'setup_ise27_data_m_src', 'setup_ise30_data_m_src'], indirect=True)
@pytest.mark.django_db
def test_ise_policies_in_database(arg):
    """Whitelisted Policies must have ISE IDs in the DB; Default Policies must have ISE IDs in the DB"""
    success = True
    default_vals = [d['name'] for d in ise_default_policies]

    sgpolicies = Policy.objects.order_by("name")
    for s in sgpolicies:
        if s.name in whitelisted_policies:
            if s.ise_id is None or s.ise_id is None:
                success = False
                print("1 (FAIL) :", model_to_dict(s))
            else:
                print("1 (SUCCESS) :", model_to_dict(s))
        if s.name in default_vals:
            if s.ise_id is None or s.ise_id is None:
                success = False
                print("2 (FAIL) :", model_to_dict(s))
            else:
                print("2 (SUCCESS) :", model_to_dict(s))

    # The default ISE ANY-ANY policy will not be synchronized to the database; subtract one for that
    if len(sgpolicies) != len(whitelisted_policies + ise_default_policies) - 1:
        success = False
        print("3 (FAIL) : ", sgpolicies, (whitelisted_policies + ise_default_policies))
    else:
        print("3 (SUCCESS) : ", sgpolicies, (whitelisted_policies + ise_default_policies))

    assert success


@pytest.mark.parametrize('arg', ['setup_ise24_data_sync_i_src', 'setup_ise26_data_sync_i_src',
                                 'setup_ise27_data_sync_i_src', 'setup_ise30_data_sync_i_src',
                                 'setup_ise24_data_sync_m_src', 'setup_ise26_data_sync_m_src',
                                 'setup_ise27_data_sync_m_src', 'setup_ise30_data_sync_m_src'], indirect=True)
@pytest.mark.django_db
def test_ise_sync_success(arg):
    """Perform a full sync and ensure SGTs, SGACLs and Policies have synced correctly"""
    success = True
    sgts = Tag.objects.all()
    for s in sgts:
        if s.tag_number in sync_tags:
            if not s.do_sync or not s.match_report(bool_only=True):
                success = False
                print("1 (FAIL) :", model_to_dict(s))
            else:
                print("1 (SUCCESS) :", model_to_dict(s))
    sgacls = ACL.objects.filter(visible=True)
    for s in sgacls:
        if s.name in expected_sgacls:
            if not s.match_report(bool_only=True):
                success = False
                print("2 (FAIL-NO_MATCH) :", model_to_dict(s))
        else:
            if s.do_sync:
                success = False
                print("2 (FAIL-SHOULD_NOT_SYNC) :", model_to_dict(s))
        if success:
            print("2 (SUCCESS) :", model_to_dict(s))
    policies = Policy.objects.all()
    for s in policies:
        if s.name in expected_policies:
            if not s.match_report(bool_only=True):
                success = False
                print("3 (FAIL-NO_MATCH) :", model_to_dict(s))
        else:
            if s.do_sync:
                success = False
                print("3 (FAIL-SHOULD_NOT_SYNC) :", model_to_dict(s))
        if success:
            print("3 (SUCCESS) :", model_to_dict(s))

    assert success
