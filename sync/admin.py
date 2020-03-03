from django.contrib import admin
from sync.models import *


class DashboardAdmin(admin.ModelAdmin):
    readonly_fields = ('raw_data', 'last_update', 'last_sync')


class ISEServerAdmin(admin.ModelAdmin):
    readonly_fields = ('raw_data', 'last_update', 'last_sync')


admin.site.register(Dashboard, DashboardAdmin)
admin.site.register(ISEServer, ISEServerAdmin)
admin.site.register(ISEMatrix)
admin.site.register(SyncSession)
admin.site.register(Tag)
admin.site.register(ACL)
admin.site.register(Policy)
