from django.contrib import admin
from django.urls import path, include
from core.views import home

urlpatterns = [
    path('admin/', admin.site.urls),

    # homepage
    path('', home),

    # API routes
    path('api/', include('core.urls')),  # ✅ IMPORTANT
]