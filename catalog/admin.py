from django.contrib import admin
from .models import Product

# configura como se ve y gestiona Product dentro de http://127.0.0.1:8000/admin/

# decorador equivalente a admin.site.register(Product, ProductAdmin)
@admin.register(Product)

# no es un modelo, es una configuración del panel admin en la que decidimos
# columndas que se ven
# filtros
# como se busca

class ProductAdmin(admin.ModelAdmin):
    #columnas, las justas y necesarias para el encargado
    list_display = ("name", "product_type", "price", "unit", "stock", "is_active")
    # el filtro se hace por fruta o verdura, o si ha o no hay stock
    list_filter = ("product_type", "is_active")

    search_fields = ("name",)
