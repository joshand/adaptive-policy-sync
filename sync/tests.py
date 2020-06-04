import pytest
from django.forms.models import model_to_dict
from .models import ISEServer, Dashboard, SyncSession, Tag, ACL, Policy
import sync._config
import meraki
from ise import ERS
from scripts.meraki_addons import meraki_read_sgt, meraki_read_sgacl, meraki_read_sgpolicy, meraki_update_sgt, \
    meraki_update_sgacl, meraki_update_sgpolicy, meraki_delete_sgt, meraki_delete_sgacl, meraki_create_sgt, \
    meraki_create_sgacl
from django.conf import settings
import scripts.dashboard_monitor
import scripts.ise_monitor
import json
from selenium import webdriver
# from selenium.webdriver.common.keys import Keys


def reset_dashboard(db):
    dashboard = meraki.DashboardAPI(base_url=db.baseurl, api_key=db.apikey, print_console=False, output_log=False,
                                    caller=settings.CUSTOM_UA)
    # default_sgts = [d['value'] for d in sync._config.meraki_default_sgts]
    # default_sgacls = [d['name'] for d in sync._config.meraki_default_sgacls]
    # default_policies = [d['name'] for d in sync._config.meraki_default_policies]

    sgts = meraki_read_sgt(dashboard, db.orgid)
    sgacls = meraki_read_sgacl(dashboard, db.orgid)
    # sgpolicies = meraki_read_sgpolicy(dashboard, db.orgid)
    for s in sgts:
        if not s["value"] in sync._config.whitelisted_sgts:
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

    sgts = meraki_read_sgt(dashboard, db.orgid)
    sgacls = meraki_read_sgacl(dashboard, db.orgid)
    sgpolicies = meraki_read_sgpolicy(dashboard, db.orgid)

    current_vals = [d['value'] for d in sgts]
    for s in sync._config.meraki_default_sgts:
        if not s["value"] in current_vals:
            print("Adding SGT", s["value"], "to Meraki Dashboard...")
            meraki_create_sgt(dashboard, db.orgid, name=s["name"], description=s["description"], value=s["value"])

    current_vals = [d['name'] for d in sgacls]
    for s in sync._config.meraki_default_sgacls:
        if not s["name"] in current_vals:
            print("Adding SGACL", s["name"], "to Meraki Dashboard...")
            meraki_create_sgacl(dashboard, db.orgid, name=s["name"], description=s["description"],
                                rules=s["aclcontent"], ipVersion=s["version"])

    sgt_list = meraki_read_sgt(dashboard, db.orgid)
    sgacl_list = meraki_read_sgacl(dashboard, db.orgid)
    current_vals = [d['name'] for d in sgpolicies]
    for pol in sync._config.meraki_default_policies:
        src_sgt_id = dst_sgt_id = None
        if not pol["name"] in current_vals:
            # Look up Policy elements that we are going to be adding in Dashboard...
            for s in sgt_list:
                if s["name"] == pol["src"]:
                    src_sgt_id = s["groupId"]
                if s["name"] == pol["dst"]:
                    dst_sgt_id = s["groupId"]
            acl_id_list = []
            for acl in pol["acls"]:
                for a in sgacl_list:
                    if a["name"] == acl:
                        acl_id_list.append(a["aclId"])

            print("Adding Egress Policy", pol["name"], "to Meraki Dashboard...")
            meraki_update_sgpolicy(dashboard, db.orgid, srcGroupId=src_sgt_id, dstGroupId=dst_sgt_id, name=pol["name"],
                                   description=pol["description"], catchAllRule=pol["default"], bindingEnabled=True,
                                   monitorModeEnabled=False, aclIds=acl_id_list)


def reset_ise(db):
    ise = ERS(ise_node=db.ipaddress, ers_user=db.username, ers_pass=db.password, verify=False, disable_warnings=True)
    default_sgts = [d['value'] for d in sync._config.ise_default_sgts]
    default_sgt_names = [d['name'] for d in sync._config.ise_default_sgts]
    default_sgacls = [d['name'] for d in sync._config.ise_default_sgacls]
    # default_policies = [d['name'] for d in sync._config.ise_default_policies]

    sgts = ise.get_sgts(detail=True)
    sgacls = ise.get_sgacls(detail=True)
    sgpolicies = ise.get_egressmatrixcells(detail=True)

    for s in sgts["response"]:
        if s["value"] in sync._config.whitelisted_sgts or (s["value"] in default_sgts and
                                                           s["name"] in default_sgt_names):
            pass
        else:
            print("Removing SGT", s["value"], "from Cisco ISE...")
            ise.delete_sgt(s["id"])

    for s in sgpolicies["response"]:
        if not s["name"] in sync._config.whitelisted_policies:
            print("Removing Egress Policy", s["name"], "from Cisco ISE...")
            ise.delete_egressmatrixcell(s["id"])

    for s in sgacls["response"]:
        if not s["name"] in (sync._config.whitelisted_sgacls + default_sgacls):
            print("Removing SGACL", s["name"], "from Cisco ISE...")
            ise.delete_sgacl(s["id"])

    sgts = ise.get_sgts(detail=True)
    sgacls = ise.get_sgacls(detail=True)
    sgpolicies = ise.get_egressmatrixcells(detail=True)

    current_vals = [d['value'] for d in sgts["response"]]
    for s in sync._config.ise_default_sgts:
        if not s["value"] in current_vals:
            print("Adding SGT", s["value"], "to Cisco ISE...")
            ise.add_sgt(s["name"], s["description"], s["value"])

    current_vals = [d['name'] for d in sgacls["response"]]
    for s in sync._config.ise_default_sgacls:
        if not s["name"] in current_vals:
            print("Adding SGACL", s["name"], "to Cisco ISE...")
            ise.add_sgacl(s["name"], s["description"], s["version"], s["aclcontent"])

    current_vals = [d['name'] for d in sgpolicies["response"]]
    for s in sync._config.ise_default_policies:
        if not s["name"] in current_vals:
            print("Adding Egress Policy", s["name"], "to Cisco ISE...")
            ise.add_egressmatrixcell(s["src"], s["dst"], s["default"], acls=s["acls"], description=s["description"])


@pytest.fixture(scope='module')
def browser(request):
    """Provide a selenium webdriver instance."""
    # SetUp
    options = webdriver.ChromeOptions()
    options.add_argument('headless')

    browser_ = webdriver.Chrome(chrome_options=options)

    yield browser_

    # TearDown
    browser_.quit()


@pytest.fixture(params=[0])
def arg(request):
    return request.getfixturevalue(request.param)


@pytest.fixture
@pytest.mark.django_db
def setup_ise24_i_src():
    cm = Dashboard.objects.create(description="Meraki", apikey=sync._config.merakiapi["apikey"],
                                  orgid=sync._config.merakiapi["orgid"],
                                  baseurl="https://api.meraki.com/api/v1")
    reset_dashboard(cm)

    ISEServer.objects.all().delete()
    s = sync._config.servers["2.4"]
    # UploadZip.objects.create(description="unittest", file=s["cert"])
    # u = Upload.objects.all()
    # print(u)

    ci = ISEServer.objects.create(description=s["desc"], ipaddress=s["ip"], username=s["user"],
                                  password=s["pass"])
    reset_ise(ci)
    SyncSession.objects.create(description="Sync", dashboard=cm, iseserver=ci, force_rebuild=True,
                               ise_source=True)


@pytest.fixture
@pytest.mark.django_db
def setup_ise26_i_src():
    cm = Dashboard.objects.create(description="Meraki", apikey=sync._config.merakiapi["apikey"],
                                  orgid=sync._config.merakiapi["orgid"],
                                  baseurl="https://api.meraki.com/api/v1")
    reset_dashboard(cm)

    ISEServer.objects.all().delete()
    s = sync._config.servers["2.6"]
    # UploadZip.objects.create(description="unittest", file=s["cert"])
    # u = Upload.objects.all()
    # print(u)

    ci = ISEServer.objects.create(description=s["desc"], ipaddress=s["ip"], username=s["user"],
                                  password=s["pass"])
    reset_ise(ci)
    SyncSession.objects.create(description="Sync", dashboard=cm, iseserver=ci, force_rebuild=True,
                               ise_source=True)


@pytest.fixture
@pytest.mark.django_db
def setup_ise27_i_src():
    cm = Dashboard.objects.create(description="Meraki", apikey=sync._config.merakiapi["apikey"],
                                  orgid=sync._config.merakiapi["orgid"],
                                  baseurl="https://api.meraki.com/api/v1")
    reset_dashboard(cm)

    ISEServer.objects.all().delete()
    s = sync._config.servers["2.7"]
    # UploadZip.objects.create(description="unittest", file=s["cert"])
    # u = Upload.objects.all()
    # print(u)

    ci = ISEServer.objects.create(description=s["desc"], ipaddress=s["ip"], username=s["user"],
                                  password=s["pass"])
    reset_ise(ci)
    SyncSession.objects.create(description="Sync", dashboard=cm, iseserver=ci, force_rebuild=True,
                               ise_source=True)


@pytest.fixture
@pytest.mark.django_db
def setup_ise30_i_src():
    cm = Dashboard.objects.create(description="Meraki", apikey=sync._config.merakiapi["apikey"],
                                  orgid=sync._config.merakiapi["orgid"],
                                  baseurl="https://api.meraki.com/api/v1")
    reset_dashboard(cm)

    ISEServer.objects.all().delete()
    s = sync._config.servers["3.0"]
    # UploadZip.objects.create(description="unittest", file=s["cert"])
    # u = Upload.objects.all()
    # print(u)

    ci = ISEServer.objects.create(description=s["desc"], ipaddress=s["ip"], username=s["user"],
                                  password=s["pass"])
    reset_ise(ci)
    SyncSession.objects.create(description="Sync", dashboard=cm, iseserver=ci, force_rebuild=True,
                               ise_source=True)


@pytest.fixture
@pytest.mark.django_db
def setup_ise24_m_src():
    cm = Dashboard.objects.create(description="Meraki", apikey=sync._config.merakiapi["apikey"],
                                  orgid=sync._config.merakiapi["orgid"],
                                  baseurl="https://api.meraki.com/api/v1")
    reset_dashboard(cm)

    ISEServer.objects.all().delete()
    s = sync._config.servers["2.4"]
    # UploadZip.objects.create(description="unittest", file=s["cert"])
    # u = Upload.objects.all()
    # print(u)

    ci = ISEServer.objects.create(description=s["desc"], ipaddress=s["ip"], username=s["user"],
                                  password=s["pass"])
    reset_ise(ci)
    SyncSession.objects.create(description="Sync", dashboard=cm, iseserver=ci, force_rebuild=True,
                               ise_source=False)


@pytest.fixture
@pytest.mark.django_db
def setup_ise26_m_src():
    cm = Dashboard.objects.create(description="Meraki", apikey=sync._config.merakiapi["apikey"],
                                  orgid=sync._config.merakiapi["orgid"],
                                  baseurl="https://api.meraki.com/api/v1")
    reset_dashboard(cm)

    ISEServer.objects.all().delete()
    s = sync._config.servers["2.6"]
    # UploadZip.objects.create(description="unittest", file=s["cert"])
    # u = Upload.objects.all()
    # print(u)

    ci = ISEServer.objects.create(description=s["desc"], ipaddress=s["ip"], username=s["user"],
                                  password=s["pass"])
    reset_ise(ci)
    SyncSession.objects.create(description="Sync", dashboard=cm, iseserver=ci, force_rebuild=True,
                               ise_source=False)


@pytest.fixture
@pytest.mark.django_db
def setup_ise27_m_src():
    cm = Dashboard.objects.create(description="Meraki", apikey=sync._config.merakiapi["apikey"],
                                  orgid=sync._config.merakiapi["orgid"],
                                  baseurl="https://api.meraki.com/api/v1")
    reset_dashboard(cm)

    ISEServer.objects.all().delete()
    s = sync._config.servers["2.7"]
    # UploadZip.objects.create(description="unittest", file=s["cert"])
    # u = Upload.objects.all()
    # print(u)

    ci = ISEServer.objects.create(description=s["desc"], ipaddress=s["ip"], username=s["user"],
                                  password=s["pass"])
    reset_ise(ci)
    SyncSession.objects.create(description="Sync", dashboard=cm, iseserver=ci, force_rebuild=True,
                               ise_source=False)


@pytest.fixture
@pytest.mark.django_db
def setup_ise30_m_src():
    cm = Dashboard.objects.create(description="Meraki", apikey=sync._config.merakiapi["apikey"],
                                  orgid=sync._config.merakiapi["orgid"],
                                  baseurl="https://api.meraki.com/api/v1")
    reset_dashboard(cm)

    ISEServer.objects.all().delete()
    s = sync._config.servers["3.0"]
    # UploadZip.objects.create(description="unittest", file=s["cert"])
    # u = Upload.objects.all()
    # print(u)

    ci = ISEServer.objects.create(description=s["desc"], ipaddress=s["ip"], username=s["user"],
                                  password=s["pass"])
    reset_ise(ci)
    SyncSession.objects.create(description="Sync", dashboard=cm, iseserver=ci, force_rebuild=True,
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
        if s.tag_number in sync._config.sync_tags:
            print("Enabling sync for tag", s.tag_number, "...")
            s.do_sync = True
            s.save()
    msg, log = scripts.ise_monitor.sync_ise()
    # print(msg, log)
    msg, log = scripts.dashboard_monitor.sync_dashboard()
    # print(msg, log)


@pytest.fixture
@pytest.mark.django_db
def setup_ise26_data_sync_i_src(setup_ise26_data_i_src):
    sgts = Tag.objects.order_by("tag_number")
    for s in sgts:
        if s.tag_number in sync._config.sync_tags:
            print("Enabling sync for tag", s.tag_number, "...")
            s.do_sync = True
            s.save()
    scripts.ise_monitor.sync_ise()
    scripts.dashboard_monitor.sync_dashboard()


@pytest.fixture
@pytest.mark.django_db
def setup_ise27_data_sync_i_src(setup_ise27_data_i_src):
    sgts = Tag.objects.order_by("tag_number")
    for s in sgts:
        if s.tag_number in sync._config.sync_tags:
            print("Enabling sync for tag", s.tag_number, "...")
            s.do_sync = True
            s.save()
    scripts.ise_monitor.sync_ise()
    scripts.dashboard_monitor.sync_dashboard()


@pytest.fixture
@pytest.mark.django_db
def setup_ise30_data_sync_i_src(setup_ise30_data_i_src):
    sgts = Tag.objects.order_by("tag_number")
    for s in sgts:
        if s.tag_number in sync._config.sync_tags:
            print("Enabling sync for tag", s.tag_number, "...")
            s.do_sync = True
            s.save()
    scripts.ise_monitor.sync_ise()
    scripts.dashboard_monitor.sync_dashboard()


@pytest.fixture
@pytest.mark.django_db
def setup_ise24_data_sync_m_src(setup_ise24_data_m_src):
    sgts = Tag.objects.order_by("tag_number")
    for s in sgts:
        if s.tag_number in sync._config.sync_tags:
            print("Enabling sync for tag", s.tag_number, "...")
            s.do_sync = True
            s.save()
    scripts.dashboard_monitor.sync_dashboard()
    scripts.ise_monitor.sync_ise()


@pytest.fixture
@pytest.mark.django_db
def setup_ise26_data_sync_m_src(setup_ise26_data_m_src):
    sgts = Tag.objects.order_by("tag_number")
    for s in sgts:
        if s.tag_number in sync._config.sync_tags:
            print("Enabling sync for tag", s.tag_number, "...")
            s.do_sync = True
            s.save()
    scripts.dashboard_monitor.sync_dashboard()
    scripts.ise_monitor.sync_ise()


@pytest.fixture
@pytest.mark.django_db
def setup_ise27_data_sync_m_src(setup_ise27_data_m_src):
    sgts = Tag.objects.order_by("tag_number")
    for s in sgts:
        if s.tag_number in sync._config.sync_tags:
            print("Enabling sync for tag", s.tag_number, "...")
            s.do_sync = True
            s.save()
    scripts.dashboard_monitor.sync_dashboard()
    scripts.ise_monitor.sync_ise()


@pytest.fixture
@pytest.mark.django_db
def setup_ise30_data_sync_m_src(setup_ise30_data_m_src):
    sgts = Tag.objects.order_by("tag_number")
    for s in sgts:
        if s.tag_number in sync._config.sync_tags:
            print("Enabling sync for tag", s.tag_number, "...")
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
def test_sgts_in_database(arg):
    """Whitelisted SGTs must have Dashboard and ISE IDs in the DB; Default SGTs must have ISE IDs in the DB"""
    success = True
    default_vals = [d['value'] for d in sync._config.ise_default_sgts]

    sgts = Tag.objects.order_by("tag_number")
    for s in sgts:
        if s.tag_number in sync._config.whitelisted_sgts:
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

    if len(sgts) != len(sync._config.whitelisted_sgts + sync._config.ise_default_sgts +
                        sync._config.meraki_default_sgts):
        success = False
        print("3 (FAIL) : ", sgts, (sync._config.whitelisted_sgts + sync._config.ise_default_sgts +
                                    sync._config.meraki_default_sgts))
    else:
        print("3 (SUCCESS) : ", sgts, (sync._config.whitelisted_sgts + sync._config.ise_default_sgts +
                                       sync._config.meraki_default_sgts))

    assert success


@pytest.mark.parametrize('arg', ['setup_ise24_data_i_src', 'setup_ise26_data_i_src', 'setup_ise27_data_i_src',
                                 'setup_ise30_data_i_src', 'setup_ise24_data_m_src', 'setup_ise26_data_m_src',
                                 'setup_ise27_data_m_src', 'setup_ise30_data_m_src'], indirect=True)
@pytest.mark.django_db
def test_sgacls_in_database(arg):
    """Whitelisted SGACLs must have ISE IDs in the DB and be invisible; Default SGACLs must have ISE IDs in the DB"""
    success = True
    default_vals = [d['name'] for d in sync._config.ise_default_sgacls]

    sgacls = ACL.objects.order_by("name")
    for s in sgacls:
        if s.name in sync._config.whitelisted_sgacls:
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

    if len(sgacls) != len(sync._config.whitelisted_sgacls + sync._config.ise_default_sgacls +
                          sync._config.meraki_default_sgacls):
        success = False
        print("3 (FAIL) : ", sgacls, (sync._config.whitelisted_sgacls + sync._config.ise_default_sgacls +
                                      sync._config.meraki_default_sgacls))
    else:
        print("3 (SUCCESS) : ", sgacls, (sync._config.whitelisted_sgacls + sync._config.ise_default_sgacls +
                                         sync._config.meraki_default_sgacls))

    assert success


@pytest.mark.parametrize('arg', ['setup_ise24_data_i_src', 'setup_ise26_data_i_src', 'setup_ise27_data_i_src',
                                 'setup_ise30_data_i_src', 'setup_ise24_data_m_src', 'setup_ise26_data_m_src',
                                 'setup_ise27_data_m_src', 'setup_ise30_data_m_src'], indirect=True)
@pytest.mark.django_db
def test_policies_in_database(arg):
    """Whitelisted Policies must have ISE IDs in the DB; Default Policies must have ISE IDs in the DB"""
    success = True
    default_vals = [d['name'] for d in sync._config.ise_default_policies]

    sgpolicies = Policy.objects.order_by("name")
    for s in sgpolicies:
        if s.name in sync._config.whitelisted_policies:
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
    if len(sgpolicies) != len(sync._config.whitelisted_policies + sync._config.ise_default_policies +
                              sync._config.meraki_default_policies) - 1:
        success = False
        print("3 (FAIL) : ", sgpolicies, (sync._config.whitelisted_policies + sync._config.ise_default_policies +
                                          sync._config.meraki_default_policies))
    else:
        print("3 (SUCCESS) : ", sgpolicies, (sync._config.whitelisted_policies + sync._config.ise_default_policies +
                                             sync._config.meraki_default_policies))

    assert success


# @pytest.mark.parametrize('arg', ['setup_ise24_data_sync_i_src', 'setup_ise26_data_sync_i_src',
#                                  'setup_ise27_data_sync_i_src', 'setup_ise30_data_sync_i_src',
#                                  'setup_ise24_data_sync_m_src', 'setup_ise26_data_sync_m_src',
#                                  'setup_ise27_data_sync_m_src', 'setup_ise30_data_sync_m_src'], indirect=True)
# @pytest.mark.django_db
# def test_ise_sync_success(arg):
#     """Perform a full sync and ensure SGTs, SGACLs and Policies have synced correctly"""
#     success = True
#     sgts = Tag.objects.all()
#     for s in sgts:
#         if s.tag_number in sync._config.sync_tags:
#             if not s.do_sync or not s.match_report(bool_only=True):
#                 success = False
#                 print("1 (FAIL) :", model_to_dict(s))
#             else:
#                 print("1 (SUCCESS) :", model_to_dict(s))
#     sgacls = ACL.objects.filter(visible=True)
#     for s in sgacls:
#         if s.name in sync._config.expected_sgacls:
#             if not s.match_report(bool_only=True):
#                 success = False
#                 print("2 (FAIL-NO_MATCH) :", model_to_dict(s))
#         else:
#             if s.do_sync:
#                 success = False
#                 print("2 (FAIL-SHOULD_NOT_SYNC) :", model_to_dict(s))
#         if success:
#             print("2 (SUCCESS) :", model_to_dict(s))
#     policies = Policy.objects.all()
#     for s in policies:
#         if s.name in sync._config.expected_policies:
#             if not s.match_report(bool_only=True):
#                 success = False
#                 print("3 (FAIL-NO_MATCH) :", model_to_dict(s))
#         else:
#             if s.do_sync:
#                 success = False
#                 print("3 (FAIL-SHOULD_NOT_SYNC) :", model_to_dict(s))
#         if success:
#             print("3 (SUCCESS) :", model_to_dict(s))
#
#     assert success


@pytest.mark.parametrize('arg', ['setup_ise24_data_sync_i_src', 'setup_ise26_data_sync_i_src',
                                 'setup_ise27_data_sync_i_src', 'setup_ise30_data_sync_i_src',
                                 'setup_ise24_data_sync_m_src', 'setup_ise26_data_sync_m_src',
                                 'setup_ise27_data_sync_m_src', 'setup_ise30_data_sync_m_src'], indirect=True)
@pytest.mark.django_db
def test_ise_sync_success(arg):
    """Perform a full sync and ensure SGTs, SGACLs and Policies have synced correctly"""
    success = True
    sgts = Tag.objects.all()
    if len(sgts) != len(sync._config.whitelisted_sgts + sync._config.ise_default_sgts +
                        sync._config.meraki_default_sgts):
        success = False
        print("1 (FAIL) :", "Incorrect number of objects in DB")
    for s in sgts:
        if s.tag_number in sync._config.sync_tags:
            if not s.do_sync or not s.match_report(bool_only=True):
                success = False
                print("1 (FAIL) :", model_to_dict(s))
            else:
                print("1 (SUCCESS) :", model_to_dict(s))
    sgacls = ACL.objects.filter(visible=True)
    if len(sgacls) != len(sync._config.ise_default_sgacls + sync._config.meraki_default_sgacls):
        success = False
        print("2 (FAIL) :", "Incorrect number of objects in DB")
    for s in sgacls:
        if s.name in sync._config.expected_ise_sgacls:
            if not s.do_sync or not s.match_report(bool_only=True):
                success = False
                print("2 (FAIL-NO_MATCH) :", model_to_dict(s))
        else:
            if s.do_sync:
                success = False
                print("2 (FAIL-SHOULD_NOT_SYNC) :", model_to_dict(s))
        if success:
            print("2 (SUCCESS) :", model_to_dict(s))
    policies = Policy.objects.all()
    if len(policies) != len(sync._config.ise_default_policies + sync._config.meraki_default_policies):
        success = False
        print("3 (FAIL) :", "Incorrect number of objects in DB")
    for s in policies:
        if s.name in sync._config.expected_ise_policies:
            if not s.do_sync or not s.match_report(bool_only=True):
                success = False
                print("3 (FAIL-NO_MATCH) :", model_to_dict(s), "\n", s.match_report())
        else:
            if s.do_sync:
                success = False
                print("3 (FAIL-SHOULD_NOT_SYNC) :", model_to_dict(s))
        if success:
            print("3 (SUCCESS) :", model_to_dict(s))

    assert success


@pytest.mark.parametrize('arg', ['setup_ise24_data_sync_i_src', 'setup_ise26_data_sync_i_src',
                                 'setup_ise27_data_sync_i_src', 'setup_ise30_data_sync_i_src',
                                 'setup_ise24_data_sync_m_src', 'setup_ise26_data_sync_m_src',
                                 'setup_ise27_data_sync_m_src', 'setup_ise30_data_sync_m_src'], indirect=True)
@pytest.mark.django_db
def test_update_element_success(arg):
    """Perform a full sync and then update each side for SGT, SGACL and Policy"""
    success = True
    sa = SyncSession.objects.all()[0]
    ci = ISEServer.objects.all()[0]
    db = Dashboard.objects.all()[0]
    ise = ERS(ise_node=ci.ipaddress, ers_user=ci.username, ers_pass=ci.password, verify=False, disable_warnings=True)
    dashboard = meraki.DashboardAPI(base_url=db.baseurl, api_key=db.apikey, print_console=False, output_log=False,
                                    caller=settings.CUSTOM_UA)

    # tag = Tag.objects.filter(name=update_sgt["search"])[0]
    # acl = ACL.objects.filter(name=update_sgacl["search"])[0]
    # policy = Policy.objects.filter(description=update_policy["search"])[0]
    # print(model_to_dict(tag))
    # print(model_to_dict(acl))
    # print(model_to_dict(policy))

    if sa.ise_source:
        upd_sgt = ise.get_sgt(sync._config.update_ise_sgt["search"])["response"]
        upd_sgacl = ise.get_sgacl(sync._config.update_ise_sgacl["search"])["response"]
        upd_policy = ise.get_egressmatrixcell(sync._config.update_ise_policy["search"])["response"]

        if not upd_sgt or not upd_sgacl or not upd_policy:
            print("One or more elements missing during search", upd_sgt, upd_sgacl, upd_policy)
            assert False

        ise.update_egressmatrixcell(upd_policy["id"], upd_policy["sourceSgtId"], upd_policy["destinationSgtId"],
                                    sync._config.update_ise_policy["default"],
                                    acls=sync._config.update_ise_policy["acls"],
                                    description=sync._config.update_ise_policy["description"])
        ise.update_sgacl(upd_sgacl["id"], sync._config.update_ise_sgacl["name"],
                         sync._config.update_ise_sgacl["description"],
                         sync._config.update_ise_sgacl["version"], sync._config.update_ise_sgacl["aclcontent"])
        ise.update_sgt(upd_sgt["id"], sync._config.update_ise_sgt["name"], sync._config.update_ise_sgt["description"],
                       sync._config.update_ise_sgt["value"])
    else:
        src_sgt_id = dst_sgt_id = update_sgt_id = update_sgacl_id = None
        # Look up SGT that we are going to be updating in Dashboard...
        sgt_list = meraki_read_sgt(dashboard, db.orgid)
        for a in sgt_list:
            if a["name"] == sync._config.update_ise_sgt["search"]:
                update_sgt_id = a["groupId"]
        # Look up SGACL that we are going to be updating in Dashboard...
        sgacl_list = meraki_read_sgacl(dashboard, db.orgid)
        for a in sgacl_list:
            # print(a["name"], update_sgacl["search"])
            if a["name"] == sync._config.update_ise_sgacl["search"]:
                update_sgacl_id = a["aclId"]
        # Look up Policy elements that we are going to be updating in Dashboard...
        for s in sgt_list:
            if s["name"] == sync._config.update_ise_policy["src"]:
                src_sgt_id = s["groupId"]
            if s["name"] == sync._config.update_ise_policy["dst"]:
                dst_sgt_id = s["groupId"]
        acl_id_list = []
        for acl in sync._config.update_ise_policy["acls"]:
            for a in sgacl_list:
                if a["name"] == acl:
                    acl_id_list.append(a["aclId"])
        # Update!
        meraki_update_sgpolicy(dashboard, db.orgid, name=sync._config.update_ise_policy["name"],
                               description=sync._config.update_ise_policy["description"], srcGroupId=src_sgt_id,
                               dstGroupId=dst_sgt_id, aclIds=acl_id_list if len(acl_id_list) > 0 else None,
                               catchAllRule=sync._config.update_ise_policy["default_meraki"], bindingEnabled=True,
                               monitorModeEnabled=False)

        acl = meraki_update_sgacl(dashboard, db.orgid, update_sgacl_id, name=sync._config.update_ise_sgacl["name"],
                                  description=sync._config.update_ise_sgacl["description"],
                                  rules=sync._config.update_ise_sgacl["aclcontent_meraki"],
                                  ipVersion=sync._config.update_ise_sgacl["version_meraki"])
        sgt = meraki_update_sgt(dashboard, db.orgid, update_sgt_id, name=sync._config.update_ise_sgt["name"],
                                description=sync._config.update_ise_sgt["description"],
                                value=sync._config.update_ise_sgt["value"])
        Tag.objects.filter(name=sync._config.update_ise_sgt["search"]).update(meraki_id=sgt["groupId"], meraki_data=sgt)

    sa.force_rebuild = True
    sa.save()
    if sa.ise_source:
        msg, log = scripts.ise_monitor.sync_ise()
        msg, log = scripts.dashboard_monitor.sync_dashboard()
    else:
        msg, log = scripts.dashboard_monitor.sync_dashboard()
        msg, log = scripts.ise_monitor.sync_ise()
    sgts = Tag.objects.filter(name=sync._config.update_ise_sgt["name"])
    if len(sgts) != 1:
        success = False
        print("1 (FAIL) :", "Incorrect number of objects in DB")
    for s in sgts:
        if s.name == sync._config.update_ise_sgt["name"] and \
                s.description == sync._config.update_ise_sgt["description"] and \
                s.tag_number == sync._config.update_ise_sgt["value"] and s.match_report(True):
            print("1 (SUCCESS) :", model_to_dict(s))
        else:
            success = False
            print("1 (FAIL) :", model_to_dict(s))
    sgacls = ACL.objects.filter(name=sync._config.update_ise_sgacl["name"])
    if len(sgacls) != 1:
        success = False
        print("2 (FAIL) :", "Incorrect number of objects in DB")
    for s in sgacls:
        ise_data = json.loads(s.ise_data)
        if s.name == sync._config.update_ise_sgacl["name"] and \
                s.description == sync._config.update_ise_sgacl["description"] and \
                s.get_version("ise") == sync._config.update_ise_sgacl["version"] and \
                ise_data["aclcontent"] == "\n".join(sync._config.update_ise_sgacl["aclcontent"]) and \
                s.match_report(True):
            print("2 (SUCCESS) :", model_to_dict(s))
        else:
            success = False
            print("2 (FAIL) :", model_to_dict(s))
    policies = Policy.objects.filter(name=sync._config.update_ise_policy["name"])
    if len(policies) != 1:
        success = False
        print("3 (FAIL) :", "Incorrect number of objects in DB")
    for s in policies:
        if s.name == sync._config.update_ise_policy["name"] and \
                s.description == sync._config.update_ise_policy["description"] and \
                s.get_catchall("meraki") == sync._config.update_ise_policy["default_meraki"] and s.match_report(True):
            print("3 (SUCCESS) :", model_to_dict(s))
        else:
            success = False
            print("3 (FAIL) :", model_to_dict(s))

    assert success


@pytest.mark.parametrize('arg', ['setup_ise24_data_sync_i_src', 'setup_ise26_data_sync_i_src',
                                 'setup_ise27_data_sync_i_src', 'setup_ise30_data_sync_i_src',
                                 'setup_ise24_data_sync_m_src', 'setup_ise26_data_sync_m_src',
                                 'setup_ise27_data_sync_m_src', 'setup_ise30_data_sync_m_src'], indirect=True)
@pytest.mark.django_db
def test_update_element_revert(arg):
    """Perform a full sync and then update wrong side for SGT, SGACL and Policy - change should get reverted"""
    success = True
    sa = SyncSession.objects.all()[0]
    ci = ISEServer.objects.all()[0]
    db = Dashboard.objects.all()[0]
    ise = ERS(ise_node=ci.ipaddress, ers_user=ci.username, ers_pass=ci.password, verify=False, disable_warnings=True)
    dashboard = meraki.DashboardAPI(base_url=db.baseurl, api_key=db.apikey, print_console=False, output_log=False,
                                    caller=settings.CUSTOM_UA)

    if not sa.ise_source:
        upd_sgt = ise.get_sgt(sync._config.update_ise_sgt["search"])["response"]
        upd_sgacl = ise.get_sgacl(sync._config.update_ise_sgacl["search"])["response"]
        upd_policy = ise.get_egressmatrixcell(sync._config.update_ise_policy["search"])["response"]

        if not upd_sgt or not upd_sgacl or not upd_policy:
            print("One or more elements missing during search", upd_sgt, upd_sgacl, upd_policy)
            assert False

        ise.update_egressmatrixcell(upd_policy["id"], upd_policy["sourceSgtId"], upd_policy["destinationSgtId"],
                                    sync._config.update_ise_policy["default"],
                                    acls=sync._config.update_ise_policy["acls"],
                                    description=sync._config.update_ise_policy["description"])
        ise.update_sgacl(upd_sgacl["id"], sync._config.update_ise_sgacl["name"],
                         sync._config.update_ise_sgacl["description"],
                         sync._config.update_ise_sgacl["version"], sync._config.update_ise_sgacl["aclcontent"])
        ise.update_sgt(upd_sgt["id"], sync._config.update_ise_sgt["name"], sync._config.update_ise_sgt["description"],
                       sync._config.update_ise_sgt["value"])
    else:
        src_sgt_id = dst_sgt_id = update_sgt_id = update_sgacl_id = None
        # Look up SGT that we are going to be updating in Dashboard...
        sgt_list = meraki_read_sgt(dashboard, db.orgid)
        for a in sgt_list:
            if a["name"] == sync._config.update_ise_sgt["search"]:
                update_sgt_id = a["groupId"]
        # Look up SGACL that we are going to be updating in Dashboard...
        sgacl_list = meraki_read_sgacl(dashboard, db.orgid)
        for a in sgacl_list:
            # print(a["name"], update_sgacl["search"])
            if a["name"] == sync._config.update_ise_sgacl["search"]:
                update_sgacl_id = a["aclId"]
        # Look up Policy elements that we are going to be updating in Dashboard...
        for s in sgt_list:
            if s["name"] == sync._config.update_ise_policy["src"]:
                src_sgt_id = s["groupId"]
            if s["name"] == sync._config.update_ise_policy["dst"]:
                dst_sgt_id = s["groupId"]
        acl_id_list = []
        for acl in sync._config.update_ise_policy["acls"]:
            for a in sgacl_list:
                if a["name"] == acl:
                    acl_id_list.append(a["aclId"])
        # Update!
        meraki_update_sgpolicy(dashboard, db.orgid, name=sync._config.update_ise_policy["name"],
                               description=sync._config.update_ise_policy["description"], srcGroupId=src_sgt_id,
                               dstGroupId=dst_sgt_id, aclIds=acl_id_list if len(acl_id_list) > 0 else None,
                               catchAllRule=sync._config.update_ise_policy["default_meraki"], bindingEnabled=True,
                               monitorModeEnabled=False)

        acl = meraki_update_sgacl(dashboard, db.orgid, update_sgacl_id, name=sync._config.update_ise_sgacl["name"],
                                  description=sync._config.update_ise_sgacl["description"],
                                  rules=sync._config.update_ise_sgacl["aclcontent_meraki"],
                                  ipVersion=sync._config.update_ise_sgacl["version_meraki"])
        sgt = meraki_update_sgt(dashboard, db.orgid, update_sgt_id, name=sync._config.update_ise_sgt["name"],
                                description=sync._config.update_ise_sgt["description"],
                                value=sync._config.update_ise_sgt["value"])
        Tag.objects.filter(name=sync._config.update_ise_sgt["search"]).update(meraki_id=sgt["groupId"], meraki_data=sgt)

    sa.force_rebuild = True
    sa.save()
    if sa.ise_source:
        msg, log = scripts.ise_monitor.sync_ise()
        msg, log = scripts.dashboard_monitor.sync_dashboard()
    else:
        msg, log = scripts.dashboard_monitor.sync_dashboard()
        msg, log = scripts.ise_monitor.sync_ise()
    sgts = Tag.objects.filter(name=sync._config.update_ise_sgt["search"])
    if len(sgts) != 1:
        success = False
        print("1 (FAIL) :", "Incorrect number of objects in DB")
    for s in sgts:
        if s.name != sync._config.update_ise_sgt["name"] and \
                s.description != sync._config.update_ise_sgt["description"] and \
                s.tag_number != sync._config.update_ise_sgt["value"] and s.match_report(True):
            print("1 (SUCCESS) :", model_to_dict(s))
        else:
            success = False
            print("1 (FAIL) :", model_to_dict(s))
    sgacls = ACL.objects.filter(name=sync._config.update_ise_sgacl["search"])
    if len(sgacls) != 1:
        success = False
        print("2 (FAIL) :", "Incorrect number of objects in DB")
    for s in sgacls:
        ise_data = json.loads(s.ise_data)
        if s.name != sync._config.update_ise_sgacl["name"] and \
                s.description != sync._config.update_ise_sgacl["description"] and \
                s.get_version("ise") != sync._config.update_ise_sgacl["version"] and \
                ise_data["aclcontent"] != "\n".join(sync._config.update_ise_sgacl["aclcontent"]) and \
                s.match_report(True):
            print("2 (SUCCESS) :", model_to_dict(s))
        else:
            success = False
            print("2 (FAIL) :", model_to_dict(s))
    policies = Policy.objects.filter(description=sync._config.update_ise_policy["search"])
    if len(policies) != 1:
        success = False
        print("3 (FAIL) :", "Incorrect number of objects in DB")
    for s in policies:
        if s.description != sync._config.update_ise_policy["description"] and s.match_report(True):
            print("3 (SUCCESS) :", model_to_dict(s))
        else:
            success = False
            print("3 (FAIL) :", model_to_dict(s), "\n", s.match_report())

    assert success


@pytest.mark.parametrize('arg', ['setup_ise24_data_sync_i_src', 'setup_ise26_data_sync_i_src',
                                 'setup_ise27_data_sync_i_src', 'setup_ise30_data_sync_i_src',
                                 'setup_ise24_data_sync_m_src', 'setup_ise26_data_sync_m_src',
                                 'setup_ise27_data_sync_m_src', 'setup_ise30_data_sync_m_src'], indirect=True)
@pytest.mark.django_db
def test_delete_element_success(arg):
    """Perform a full sync and then delete SGT, SGACL and Policy from each side"""
    success = True
    sa = SyncSession.objects.all()[0]
    ci = ISEServer.objects.all()[0]
    db = Dashboard.objects.all()[0]
    ise = ERS(ise_node=ci.ipaddress, ers_user=ci.username, ers_pass=ci.password, verify=False, disable_warnings=True)
    dashboard = meraki.DashboardAPI(base_url=db.baseurl, api_key=db.apikey, print_console=False, output_log=False,
                                    caller=settings.CUSTOM_UA)

    if sa.ise_source:
        upd_sgt = ise.get_sgt(sync._config.update_ise_sgt["search"])["response"]
        upd_sgacl = ise.get_sgacl(sync._config.update_ise_sgacl["search"])["response"]
        upd_policy = ise.get_egressmatrixcell(sync._config.update_ise_policy["search"])["response"]

        if not upd_sgt or not upd_sgacl or not upd_policy:
            print("One or more elements missing during search", upd_sgt, upd_sgacl, upd_policy)
            assert False

        ise.delete_egressmatrixcell(upd_policy["id"])
        ise.delete_sgacl(upd_sgacl["id"])
        ise.delete_sgt(upd_sgt["id"])
    else:
        src_sgt_id = dst_sgt_id = update_sgt_id = update_sgacl_id = None
        # Look up SGT that we are going to be updating in Dashboard...
        sgt_list = meraki_read_sgt(dashboard, db.orgid)
        # print("#####", sgt_list)
        for a in sgt_list:
            if a["name"] == sync._config.update_ise_sgt["search"]:
                update_sgt_id = a["groupId"]
                # t = Tag.objects.filter(name=a["name"])
                # print(a["name"], sync._config.update_ise_sgt["search"], update_sgt_id, model_to_dict(t[0]))
                break
        # Look up SGACL that we are going to be updating in Dashboard...
        sgacl_list = meraki_read_sgacl(dashboard, db.orgid)
        # print("#####", sgacl_list)
        for a in sgacl_list:
            # print(a["name"], sync._config.update_ise_sgacl["search"])
            if a["name"] == sync._config.update_ise_sgacl["search"]:
                update_sgacl_id = a["aclId"]
        # Look up Policy elements that we are going to be updating in Dashboard...
        for s in sgt_list:
            if s["name"] == sync._config.update_ise_policy["src"]:
                src_sgt_id = s["groupId"]
            if s["name"] == sync._config.update_ise_policy["dst"]:
                dst_sgt_id = s["groupId"]
        acl_id_list = []
        for acl in sync._config.update_ise_policy["acls"]:
            for a in sgacl_list:
                if a["name"] == acl:
                    acl_id_list.append(a["aclId"])
        # Delete!
        meraki_update_sgpolicy(dashboard, db.orgid, name=sync._config.update_ise_policy["search"],
                               description=sync._config.update_ise_policy["description"], srcGroupId=src_sgt_id,
                               dstGroupId=dst_sgt_id, aclIds=None, catchAllRule="global")
        meraki_delete_sgacl(dashboard, db.orgid, update_sgacl_id)
        meraki_delete_sgt(dashboard, db.orgid, update_sgt_id)
        # print(update_sgt_id, sgt)
        # Tag.objects.filter(name=sync._config.update_ise_sgt["search"]).update(meraki_id=None, meraki_data=None)

    sa.force_rebuild = True
    sa.save()
    if sa.ise_source:
        msg, log = scripts.ise_monitor.sync_ise()
        # print("ise---------", msg, log)
        msg, log = scripts.dashboard_monitor.sync_dashboard()
        # print("meraki---------", msg, log)
    else:
        msg, log = scripts.dashboard_monitor.sync_dashboard()
        # print("meraki---------", msg, log)
        msg, log = scripts.ise_monitor.sync_ise()
        # print("ise---------", msg, log)

    # m_sgt_list = meraki_read_sgt(dashboard, db.orgid)
    # i_sgt_list = ise.get_sgts(detail=True)
    #
    # sgts = Tag.objects.all()
    # print(sgts, m_sgt_list, i_sgt_list)

    sgts = Tag.objects.filter(name=sync._config.update_ise_sgt["search"])
    if len(sgts) != 0:
        success = False
        print("1 (FAIL) :", "Incorrect number of objects in DB")
    else:
        print("1 (SUCCESS) :", "Element deleted from DB")
    sgacls = ACL.objects.filter(name=sync._config.update_ise_sgacl["search"])
    if len(sgacls) != 0:
        success = False
        print("2 (FAIL) :", "Incorrect number of objects in DB")
    else:
        print("2 (SUCCESS) :", "Element deleted from DB")
    policies = Policy.objects.filter(description=sync._config.update_ise_policy["search"])
    if len(policies) != 0:
        success = False
        print("3 (FAIL) :", "Incorrect number of objects in DB")
    else:
        print("3 (SUCCESS) :", "Element deleted from DB")

    assert success


@pytest.mark.parametrize('arg', ['setup_ise24_data_sync_i_src', 'setup_ise26_data_sync_i_src',
                                 'setup_ise27_data_sync_i_src', 'setup_ise30_data_sync_i_src',
                                 'setup_ise24_data_sync_m_src', 'setup_ise26_data_sync_m_src',
                                 'setup_ise27_data_sync_m_src', 'setup_ise30_data_sync_m_src'], indirect=True)
@pytest.mark.django_db
def test_delete_element_revert(arg):
    """Perform a full sync and then delete SGT, SGACL and Policy from each non-auth size; change should be reverted"""
    success = True
    sa = SyncSession.objects.all()[0]
    ci = ISEServer.objects.all()[0]
    db = Dashboard.objects.all()[0]
    ise = ERS(ise_node=ci.ipaddress, ers_user=ci.username, ers_pass=ci.password, verify=False, disable_warnings=True)
    dashboard = meraki.DashboardAPI(base_url=db.baseurl, api_key=db.apikey, print_console=False, output_log=False,
                                    caller=settings.CUSTOM_UA)

    if not sa.ise_source:
        upd_sgt = ise.get_sgt(sync._config.update_ise_sgt["search"])["response"]
        upd_sgacl = ise.get_sgacl(sync._config.update_ise_sgacl["search"])["response"]
        upd_policy = ise.get_egressmatrixcell(sync._config.update_ise_policy["search"])["response"]

        if not upd_sgt or not upd_sgacl or not upd_policy:
            print("One or more elements missing during search", upd_sgt, upd_sgacl, upd_policy)
            assert False

        ise.delete_egressmatrixcell(upd_policy["id"])
        ise.delete_sgacl(upd_sgacl["id"])
        ise.delete_sgt(upd_sgt["id"])
    else:
        src_sgt_id = dst_sgt_id = update_sgt_id = update_sgacl_id = None
        # Look up SGT that we are going to be updating in Dashboard...
        sgt_list = meraki_read_sgt(dashboard, db.orgid)
        # print("#####", sgt_list)
        for a in sgt_list:
            if a["name"] == sync._config.update_ise_sgt["search"]:
                update_sgt_id = a["groupId"]
                # t = Tag.objects.filter(name=a["name"])
                # print(a["name"], sync._config.update_ise_sgt["search"], update_sgt_id, model_to_dict(t[0]))
                break
        # Look up SGACL that we are going to be updating in Dashboard...
        sgacl_list = meraki_read_sgacl(dashboard, db.orgid)
        # print("#####", sgacl_list)
        for a in sgacl_list:
            # print(a["name"], sync._config.update_ise_sgacl["search"])
            if a["name"] == sync._config.update_ise_sgacl["search"]:
                update_sgacl_id = a["aclId"]
        # Look up Policy elements that we are going to be updating in Dashboard...
        for s in sgt_list:
            if s["name"] == sync._config.update_ise_policy["src"]:
                src_sgt_id = s["groupId"]
            if s["name"] == sync._config.update_ise_policy["dst"]:
                dst_sgt_id = s["groupId"]
        acl_id_list = []
        for acl in sync._config.update_ise_policy["acls"]:
            for a in sgacl_list:
                if a["name"] == acl:
                    acl_id_list.append(a["aclId"])
        # Delete!
        meraki_update_sgpolicy(dashboard, db.orgid, name=sync._config.update_ise_policy["search"],
                               description=sync._config.update_ise_policy["description"], srcGroupId=src_sgt_id,
                               dstGroupId=dst_sgt_id, aclIds=None, catchAllRule="global")
        meraki_delete_sgacl(dashboard, db.orgid, update_sgacl_id)
        meraki_delete_sgt(dashboard, db.orgid, update_sgt_id)
        # print(update_sgt_id, sgt)
        # Tag.objects.filter(name=sync._config.update_ise_sgt["search"]).update(meraki_id=None, meraki_data=None)

    sa.force_rebuild = True
    sa.save()
    if sa.ise_source:
        msg, log = scripts.ise_monitor.sync_ise()
        # print("ise---------", msg, log)
        msg, log = scripts.dashboard_monitor.sync_dashboard()
        # print("meraki---------", msg, log)
    else:
        msg, log = scripts.dashboard_monitor.sync_dashboard()
        # print("meraki---------", msg, log)
        msg, log = scripts.ise_monitor.sync_ise()
        # print("ise---------", msg, log)

    # m_sgt_list = meraki_read_sgt(dashboard, db.orgid)
    # i_sgt_list = ise.get_sgts(detail=True)
    #
    # sgts = Tag.objects.all()
    # print(sgts, m_sgt_list, i_sgt_list)

    sgts = Tag.objects.filter(name=sync._config.update_ise_sgt["search"])
    if len(sgts) != 1:
        success = False
        print("1 (FAIL) :", "Incorrect number of objects in DB")
    else:
        print("1 (SUCCESS) :", "Element deleted from DB")
    sgacls = ACL.objects.filter(name=sync._config.update_ise_sgacl["search"])
    if len(sgacls) != 1:
        success = False
        print("2 (FAIL) :", "Incorrect number of objects in DB")
    else:
        print("2 (SUCCESS) :", "Element deleted from DB")
    policies = Policy.objects.filter(description=sync._config.update_ise_policy["search"])
    if len(policies) != 1:
        success = False
        print("3 (FAIL) :", "Incorrect number of objects in DB")
    else:
        print("3 (SUCCESS) :", "Element deleted from DB")

    assert success


# @pytest.mark.parametrize('arg', ['setup_ise24_i_src', 'setup_ise26_i_src', 'setup_ise27_i_src', 'setup_ise30_i_src'],
#                          indirect=True)
# @pytest.mark.django_db
# def test_ui_setup(arg):
#     driver = webdriver.Firefox()
#     driver.get('http://127.0.0.1:8000')
#     username = driver.find_element_by_id('username')
#     password = driver.find_element_by_id('id_password')
#     submit = driver.find_element_by_tag_name('button')
#     username.send_keys('unittests')
#     password.send_keys('Phg7aCyItk4QMk')
#     submit.send_keys(Keys.RETURN)
