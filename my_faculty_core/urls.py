"""
URL configuration for my_faculty_core project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.1/topics/http/urls/
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
"""
URL configuration for my_faculty_core project.
Routes main traffic to faculty_app views.
"""

from django.contrib import admin
from django.urls import path, include
from faculty_app.views import set_language_view

urlpatterns = [
    # Django Administration Panel
    path('admin/', admin.site.urls),
    
    # Language switcher
    path('set-lang/<str:lang_code>', set_language_view, name='set_language'),
    
    # Faculty ERP App Routes (sve rute su u faculty_app/urls.py)
    path('', include('faculty_app.urls')),
]