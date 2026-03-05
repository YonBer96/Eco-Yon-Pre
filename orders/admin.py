from django.contrib import admin
from .models import Order, OrderItem


class OrderItemInline(admin.TabularInline):
    """
    Configuración para mostrar los productos de un pedido
    dentro del propio pedido en el panel de administración.

    Permite ver (y editar) los OrderItem directamente
    desde la pantalla del Order.
    """
    model = OrderItem   # Modelo que se mostrará en línea
    extra = 0           # No mostrar filas vacías extra por defecto


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    """
    Configuración del modelo Order en el panel de administración.

    Define cómo se listan y cómo se muestran los pedidos.
    """

    # Columnas visibles en el listado de pedidos
    list_display = ("id", "user", "status", "created_at")

    # Filtros laterales del admin
    list_filter = ("status",)

    # Muestra los OrderItem dentro del pedido
    inlines = [OrderItemInline]
