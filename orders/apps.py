from django.apps import AppConfig


class OrdersConfig(AppConfig):
    """
    Configuración de la app 'orders'.

    Django usa esta clase para:
    - registrar la app
    - cargarla al iniciar el proyecto
    - aplicar configuraciones internas
    """

    # Tipo de campo automático por defecto para IDs
    default_auto_field = 'django.db.models.BigAutoField'

    # Nombre de la app (debe coincidir con la carpeta)
    name = 'orders'
