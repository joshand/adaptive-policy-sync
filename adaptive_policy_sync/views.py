from sync.models import ISEServer, Upload, UploadZip, Dashboard, Tag, ACL, Policy, SyncSession
from django.shortcuts import redirect, reverse, render
from django.contrib.auth import logout
from django.http import JsonResponse
from django.contrib.auth import views as auth_views
from .forms import UploadForm
import meraki


def getmerakiorgs(request):
    dashboards = Dashboard.objects.all()
    if len(dashboards) > 0:
        dashboard = dashboards[0]
        baseurl = dashboard.baseurl
    else:
        dashboard = None
        baseurl = "https://api-mp.meraki.com/api/v0"

    apikey = request.headers.get("X-Cisco-Meraki-API-Key")

    try:
        dashboard = meraki.DashboardAPI(base_url=baseurl, api_key=apikey,
                                        print_console=False, output_log=False)
        orgs = dashboard.organizations.getOrganizations()
        orgs_sorted = sorted(orgs, key=lambda i: i['name'])
        return JsonResponse(orgs_sorted, safe=False)
    except Exception:
        return JsonResponse({}, safe=False)


def dolanding(request):
    if not request.user.is_authenticated:
        return redirect('/login')

    syncs = SyncSession.objects.all()
    if len(syncs) > 0:
        sync = syncs[0]
    else:
        sync = None

    if sync:
        return redirect("/home")
    else:
        return redirect("/setup")


def setup(request):
    if not request.user.is_authenticated:
        return redirect('/login')

    return render(request, 'setup/landing.html', {"active": 1})


def setupise(request):
    if not request.user.is_authenticated:
        return redirect('/login')

    iseservers = ISEServer.objects.all()
    if len(iseservers) > 0:
        iseserver = iseservers[0]
    else:
        iseserver = None

    return render(request, 'setup/ise.html', {"active": 2, "data": iseserver})


def setupisenext(request):
    if not request.user.is_authenticated:
        return redirect('/login')

    iseservers = ISEServer.objects.all()
    if len(iseservers) > 0:
        iseserver = iseservers[0]
    else:
        iseserver = None

    if request.method == 'POST':
        iseip = request.POST.get("iseIP")
        iseun = request.POST.get("iseUser")
        isepw = request.POST.get("isePass")
        pxgrid_post = request.POST.get("use_pxgrid")
        if pxgrid_post:
            pxgrid = True
        else:
            pxgrid = False

        if iseip and iseun and isepw:
            if iseserver:
                iseserver.ipaddress = iseip
                iseserver.username = iseun
                iseserver.password = isepw
                iseserver.pxgrid_enable = pxgrid
                iseserver.save()
            else:
                ISEServer.objects.create(description="ISE Server", ipaddress=iseip, username=iseun, password=isepw,
                                         pxgrid_enable=pxgrid)
        else:
            print("ISE Server: missing fields")

        if pxgrid:
            return redirect('/setup/isecert')
        else:
            return redirect('/setup/meraki')
    else:
        return redirect('/setup/isecert')


def setupcert(request):
    if not request.user.is_authenticated:
        return redirect('/login')

    # iseservers = ISEServer.objects.all()
    # if len(iseservers) > 0:
    #     iseserver = iseservers[0]
    # else:
    #     iseserver = None
    uploadzips = Upload.objects.all()

    if request.method == 'POST':
        form = UploadForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('/home')
    else:
        form = UploadForm()
    return render(request, 'setup/isecert.html', {"active": 3, "data": uploadzips, "form": form})


def setuppxgrid(request):
    if not request.user.is_authenticated:
        return redirect('/login')

    iseservers = ISEServer.objects.all()
    if len(iseservers) > 0:
        iseserver = iseservers[0]
    else:
        iseserver = None

    uploads = Upload.objects.all().exclude(description__contains="CertificateServices")
    return render(request, 'setup/isepxgrid.html', {"active": 4, "data": iseserver, "upload": uploads})


def setupmeraki(request):
    if not request.user.is_authenticated:
        return redirect('/login')

    dashboards = Dashboard.objects.all()
    if len(dashboards) > 0:
        dashboard = dashboards[0]
    else:
        dashboard = None

    iseservers = ISEServer.objects.all()
    if len(iseservers) > 0:
        iseserver = iseservers[0]
    else:
        iseserver = None

    if request.method == 'POST':
        pxgridip = request.POST.get("pxgridIP")
        pxgridcli = request.POST.get("pxgridClient")
        pxgridpw = request.POST.get("pxgridPassword")
        client_certid = request.POST.get("clientcertid")
        client_keyid = request.POST.get("clientkeyid")
        server_certid = request.POST.get("servercertid")
        cli_cert = Upload.objects.filter(id=client_certid)
        cli_key = Upload.objects.filter(id=client_keyid)
        server_cert = Upload.objects.filter(id=server_certid)

        if pxgridip and pxgridcli and pxgridpw and len(cli_cert) > 0 and len(cli_key) > 0 and len(server_cert) > 0:
            if iseserver:
                iseserver.pxgrid_ip = pxgridip
                iseserver.pxgrid_cliname = pxgridcli
                iseserver.pxgrid_clicert = pxgridpw
                iseserver.pxgrid_clikey = cli_cert[0]
                iseserver.pxgrid_clipw = cli_key[0]
                iseserver.pxgrid_isecert = server_cert[0]
                iseserver.save()

    return render(request, 'setup/meraki.html', {"active": 5, "data": dashboard})


def setupsync(request):
    if not request.user.is_authenticated:
        return redirect('/login')

    syncs = SyncSession.objects.all()
    if len(syncs) > 0:
        sync = syncs[0]
    else:
        sync = None

    dashboards = Dashboard.objects.all()
    if len(dashboards) > 0:
        dashboard = dashboards[0]
    else:
        dashboard = None

    if request.method == 'POST':
        apikey = request.POST.get("apiKey")
        orgid = request.POST.get("orgid")
        if apikey and orgid:
            if dashboard:
                dashboard.apikey = apikey
                dashboard.orgid = orgid
                dashboard.save()
            else:
                Dashboard.objects.create(description="Meraki Dashboard", apikey=apikey, orgid=orgid)

    return render(request, 'setup/sync.html', {"active": 6, "data": sync})


def setupdone(request):
    if not request.user.is_authenticated:
        return redirect('/login')

    syncs = SyncSession.objects.all()
    if len(syncs) > 0:
        sync = syncs[0]
    else:
        sync = None

    iseservers = ISEServer.objects.all()
    if len(iseservers) > 0:
        iseserver = iseservers[0]
    else:
        iseserver = None

    dashboards = Dashboard.objects.all()
    if len(dashboards) > 0:
        dashboard = dashboards[0]
    else:
        dashboard = None

    if request.method == 'POST':
        source = request.POST.get("basicRadio")
        sync_int = request.POST.get("syncInterval")
        if source.lower() == "ise":
            ise_source = True
        else:
            ise_source = False

        if sync_int:
            if sync and iseserver and dashboard:
                sync.ise_source = ise_source
                sync.sync_interval = sync_int
                sync.save()
            else:
                SyncSession.objects.create(description="TrustSec Sync", dashboard=dashboard, iseserver=iseserver,
                                           ise_source=ise_source, sync_interval=sync_int)

    return redirect("/home")


def home(request):
    if not request.user.is_authenticated:
        return redirect('/login')

    crumbs = '<li class="current">Home</li>'
    return render(request, 'home/home.html', {"crumbs": crumbs})


def sgtstatus(request):
    if not request.user.is_authenticated:
        return redirect('/login')

    pk = request.GET.get("id")
    if pk:
        sgts = Tag.objects.filter(id=pk)
        if len(sgts) == 1:
            sgt = sgts[0]
            desc = sgt.name + " (" + str(sgt.tag_number) + ")"
            crumbs = '''
                <li class="current">Status</li>
                <li><a href="/home/status-sgt">SGTs</a></li>
                <li class="current">''' + desc + '''</li>
            '''
            return render(request, 'home/showsgt.html', {"crumbs": crumbs, "menuopen": 1, "data": sgt})

    sgts = Tag.objects.all()
    crumbs = '<li class="current">Status</li><li class="current">SGTs</li>'
    return render(request, 'home/sgtstatus.html', {"crumbs": crumbs, "menuopen": 1, "data": {"sgt": sgts}})


def sgaclstatus(request):
    if not request.user.is_authenticated:
        return redirect('/login')

    pk = request.GET.get("id")
    if pk:
        sgacls = ACL.objects.filter(id=pk)
        if len(sgacls) == 1:
            sgacl = sgacls[0]
            desc = sgacl.name
            crumbs = '''
                <li class="current">Status</li>
                <li><a href="/home/status-sgacl">SGACLs</a></li>
                <li class="current">''' + desc + '''</li>
            '''
            return render(request, 'home/showsgacl.html', {"crumbs": crumbs, "menuopen": 1, "data": sgacl})

    sgacls = ACL.objects.all()
    crumbs = '<li class="current">Status</li><li class="current">SGACLs</li>'
    return render(request, 'home/sgaclstatus.html', {"crumbs": crumbs, "menuopen": 1, "data": {"sgacl": sgacls}})


def policystatus(request):
    if not request.user.is_authenticated:
        return redirect('/login')

    pk = request.GET.get("id")
    if pk:
        policies = Policy.objects.filter(id=pk)
        if len(policies) == 1:
            policy = policies[0]
            desc = policy.name + " (" + str(policy.mapping) + ")"
            crumbs = '''
                <li class="current">Status</li>
                <li><a href="/home/status-policy">Policies</a></li>
                <li class="current">''' + desc + '''</li>
            '''
            return render(request, 'home/showpolicy.html', {"crumbs": crumbs, "menuopen": 1, "data": policy})

    policies = Policy.objects.all()
    crumbs = '<li class="current">Status</li><li class="current">Policies</li>'
    return render(request, 'home/policystatus.html', {"crumbs": crumbs, "menuopen": 1, "data": {"policy": policies}})


def certconfig(request):
    if not request.user.is_authenticated:
        return redirect('/login')

    uploadzip = UploadZip.objects.all()
    upload = Upload.objects.all()

    crumbs = '<li class="current">Configuration</li><li class="current">Certificates</li>'
    return render(request, 'home/certconfig.html', {"crumbs": crumbs, "menuopen": 2,
                                                    "data": {"zip": uploadzip, "file": upload}})


def iseconfig(request):
    if not request.user.is_authenticated:
        return redirect('/login')

    iseservers = ISEServer.objects.all()
    if len(iseservers) > 0:
        iseserver = iseservers[0]
    else:
        iseserver = None

    crumbs = '<li class="current">Configuration</li><li class="current">ISE Server</li>'
    return render(request, 'home/iseconfig.html', {"crumbs": crumbs, "menuopen": 2, "data": iseserver})


def merakiconfig(request):
    if not request.user.is_authenticated:
        return redirect('/login')

    dashboards = Dashboard.objects.all()
    if len(dashboards) > 0:
        dashboard = dashboards[0]
    else:
        dashboard = None

    crumbs = '<li class="current">Configuration</li><li class="current">Meraki Dashboard</li>'
    return render(request, 'home/merakiconfig.html', {"crumbs": crumbs, "menuopen": 2, "data": dashboard})


def syncconfig(request):
    if not request.user.is_authenticated:
        return redirect('/login')

    syncs = SyncSession.objects.all()
    if len(syncs) > 0:
        sync = syncs[0]
    else:
        sync = None

    crumbs = '<li class="current">Configuration</li><li class="current">Synchronization</li>'
    return render(request, 'home/syncconfig.html', {"crumbs": crumbs, "menuopen": 2, "data": sync})


class MyLoginView(auth_views.LoginView):
    template_name = "general/login.html"

    def get_context_data(self, **kwargs):
        context = super(MyLoginView, self).get_context_data(**kwargs)
        return context

    def get_success_url(self):
        return reverse('landing')


class MyLogoutView(auth_views.LogoutView):
    def dispatch(self, request, *args, **kwargs):
        logout(request)
        return redirect('/')
