# -*- coding: utf-8 -*-
"""
URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.9/topics/http/urls/

Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf.urls import url
from django.contrib import admin
from django.contrib.auth import views as auth_views

login_view = auth_views.LoginView.as_view() if hasattr(auth_views, 'LoginView') else auth_views.login
logout_view = auth_views.LogoutView.as_view() if hasattr(auth_views, 'LogoutView') else auth_views.logout

urlpatterns = [
    url(r'^login/$', login_view, {'template_name': 'login.html'}, name="login"),
    url(r'^logout/$', logout_view, name="logout"),
    url(r'^admin/', admin.site.urls),
]
