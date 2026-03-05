from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from .api_views import RegisterView, MeView

# definimos los endpoints relacionados con usuarios y JWT
# conecta URLS de la API con las vistas
# registro de usuarios
# obtener datos del usuairo logueado    
# login con JWT
# refrescar el token JWT

urlpatterns = [
    path("register/", RegisterView.as_view(), name="api_register"),
    path("me/", MeView.as_view(), name="api_me"),
    path("token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
]
