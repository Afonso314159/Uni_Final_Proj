"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
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
from django.urls import include, path
from com_soc import views as com_soc_views, stripe_views
from django.conf.urls.static import static
from django.conf import settings
 
urlpatterns = [
    path('', com_soc_views.landing_page, name='landing_page'),
    path('com_soc/', include('com_soc.urls')),
    path('admin/', admin.site.urls),
    path('', include('django.contrib.auth.urls')),   # login, logout, password_reset, etc.
    path('register/', com_soc_views.register, name='register'),
    path('verify-email/<uidb64>/<token>/', com_soc_views.verify_email, name='verify_email'),
    path('webhooks/stripe/',      stripe_views.stripe_webhook,         name='stripe_webhook'),

] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
 