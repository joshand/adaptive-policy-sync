from django.db import models
import django.utils.timezone
import uuid


class Dashboard(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    description = models.CharField("Dashboard Integration Description", max_length=100, blank=False, null=False)
    baseurl = models.CharField(max_length=64, null=False, blank=False, default="https://api.meraki.com/api/v0")
    apikey = models.CharField(max_length=64, null=False, blank=False)
    orgid = models.CharField(max_length=32, null=True, blank=True, default=None)
    # netid = models.CharField(max_length=32, null=True, blank=True, default=None)
    # username = models.CharField(max_length=64, null=True, blank=True, default=None)
    # password = models.CharField(max_length=64, null=True, blank=True, default=None)
    raw_data = models.TextField(blank=True, null=True, default=None)
    force_rebuild = models.BooleanField("Force Dashboard Sync", default=False, editable=True)
    skip_sync = models.BooleanField(default=False, editable=False)
    last_update = models.DateTimeField(default=django.utils.timezone.now)
    last_sync = models.DateTimeField(null=True, default=None, blank=True)

    def __str__(self):
        return self.description


class ISEServer(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    description = models.CharField("ISE Server Description", max_length=100, blank=False, null=False)
    ipaddress = models.CharField(max_length=64, null=False, blank=False)
    username = models.CharField(max_length=64, null=True, blank=True, default=None)
    password = models.CharField(max_length=64, null=True, blank=True, default=None)
    raw_data = models.TextField(blank=True, null=True, default=None)
    force_rebuild = models.BooleanField("Force Server Sync", default=False, editable=True)
    skip_sync = models.BooleanField(default=False, editable=False)
    last_update = models.DateTimeField(default=django.utils.timezone.now)
    last_sync = models.DateTimeField(null=True, default=None, blank=True)

    def __str__(self):
        return self.description


class ISEMatrix(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    ise_id = models.CharField(max_length=64, null=False, blank=False)
    name = models.CharField(max_length=64, null=False, blank=False)
    iseserver = models.ForeignKey(ISEServer, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return self.name


class SyncSession(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    description = models.CharField("Sync Description", max_length=100, blank=False, null=False)
    dashboard = models.ForeignKey(Dashboard, on_delete=models.SET_NULL, null=True, blank=True)
    isematrix = models.ForeignKey(ISEMatrix, on_delete=models.SET_NULL, null=True, blank=True)
    ise_source = models.BooleanField("Is ISE Config base?", default=True, editable=True)

    def __str__(self):
        return self.description


class Tag(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField("Tag Name", max_length=50, blank=False, null=False)
    description = models.CharField("Tag Description", max_length=100, blank=False, null=False)
    do_sync = models.BooleanField("Sync this Tag?", default=False, editable=True)
    tag_number = models.IntegerField(blank=False, null=False, default=0)
    src_data = models.TextField(blank=True, null=True, default=None)
    dst_data = models.TextField(blank=True, null=True, default=None)
    last_update = models.DateTimeField(default=django.utils.timezone.now)

    def __str__(self):
        return self.name + " (" + str(self.tag_number) + ")"


class ACL(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField("Tag Name", max_length=50, blank=False, null=False)
    description = models.CharField("Tag Description", max_length=100, blank=False, null=False)
    # do_sync = models.BooleanField("Sync this Tag?", default=False, editable=True)
    src_data = models.TextField(blank=True, null=True, default=None)
    dst_data = models.TextField(blank=True, null=True, default=None)
    last_update = models.DateTimeField(default=django.utils.timezone.now)

    def __str__(self):
        return self.name


class Policy(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField("Policy Name", max_length=50, blank=False, null=False)
    description = models.CharField("Policy Description", max_length=100, blank=False, null=False)
    # do_sync = models.BooleanField("Sync this Tag?", default=False, editable=True)
    src_data = models.TextField(blank=True, null=True, default=None)
    dst_data = models.TextField(blank=True, null=True, default=None)
    last_update = models.DateTimeField(default=django.utils.timezone.now)

    def __str__(self):
        return self.name
