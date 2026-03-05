"""
Archivo principal de rutas del proyecto Eco-Yon.

Aquí se conectan:
- el panel de administración
- las páginas HTML
- la API
- el dashboard
- los archivos media en desarrollo
"""

from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView
from django.conf import settings
from django.conf.urls.static import static
from orders.manager_api_views import manager_albaran_summary,manager_albaran_summary_pdf 
from django.contrib.auth import views as auth_views

urlpatterns = [

    # =========================
    # ADMIN DE DJANGO
    # =========================
    path('admin/', admin.site.urls),


    # =========================
    # PÁGINAS HTML
    # =========================

    # Redirección de la raíz "/" a "/products/"
    path("", RedirectView.as_view(url="/products/", permanent=False)),

    # Rutas HTML (login, register, products, cart, checkout, etc.)
    path("", include("pages.urls")),


    # =========================
    # API REST
    # =========================

    # Endpoints de cuentas (register, login, me, refresh...)
    path("api/", include("accounts.api_urls")),

    # Endpoints de productos
    path("api/", include("catalog.api_urls")),

    # Endpoints de carrito, pedidos, facturas, manager...
    path("api/", include("orders.api_urls")),


    # =========================
    # DASHBOARD (ENCARGADO)
    # =========================

    # Rutas HTML del panel de gestión
    path("dashboard/", include("dashboard.urls")),

    path("staff/login/", auth_views.LoginView.as_view(template_name="pages/staff_login.html"), name="staff_login"),
    path("staff/logout/", auth_views.LogoutView.as_view(next_page="/staff/login/"), name="staff_logout"),

    
]


# Permite servir imágenes subidas (productos, facturas, etc.)
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
