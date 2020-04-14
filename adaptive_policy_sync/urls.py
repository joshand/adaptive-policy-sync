"""adaptive_policy_sync URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from django.conf.urls import url, include
from rest_framework import routers
from rest_framework.authtoken.views import obtain_auth_token
from rest_framework.schemas import get_schema_view
from rest_framework.renderers import JSONOpenAPIRenderer
from sync import views
from adaptive_policy_sync import tasks
tasks.run_tasks()
from scripts.dashboard_webhook import process_webhook

router = routers.DefaultRouter()
router.register(r'api/v0/uploadzip', views.UploadZipViewSet)
router.register(r'api/v0/upload', views.UploadViewSet)
router.register(r'api/v0/dashboard', views.DashboardViewSet)
router.register(r'api/v0/iseserver', views.ISEServerViewSet)
# router.register(r'api/v0/isematrix', views.ISEMatrixViewSet)
router.register(r'api/v0/syncsession', views.SyncSessionViewSet)
router.register(r'api/v0/tag', views.TagViewSet)
router.register(r'api/v0/acl', views.ACLViewSet)
router.register(r'api/v0/policy', views.PolicyViewSet)

schema_view = get_schema_view(title="Adaptive Policy Sync API", renderer_classes=[JSONOpenAPIRenderer])

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api-auth/', include('rest_framework.urls', namespace='rest_framework')),
    path('api-token-auth/', obtain_auth_token, name='api_token_auth'),
    path('api/v0/schema/', schema_view),
    path('webhook/', process_webhook),
    path('', include(router.urls)),
]
