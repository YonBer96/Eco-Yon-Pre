from rest_framework import generics, permissions
from .models import Product
from .serializers import ProductSerializer


class ProductListView(generics.ListAPIView):
    """
    Endpoint de solo lectura para listar productos del catálogo.

    Devuelve productos activos y permite:
    - filtrar por tipo (FRUTA / VERDURA)
    - buscar por nombre
    """

    # Serializer que convierte Product en JSON
    serializer_class = ProductSerializer

    # Solo usuarios autenticados pueden acceder
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_context(self):
        """
        Añade el request al contexto del serializer.

        Se usa para que el ProductSerializer pueda construir
        URLs absolutas de las imágenes.
        """
        context = super().get_serializer_context()
        context["request"] = self.request
        return context

    def get_queryset(self):
        """
        Construye el queryset de productos que se enviará al frontend.

        - Solo productos activos
        - Ordenados por nombre
        - Permite filtros por query params:
            ?q=manzana
            ?product_type=FRUTA
        """

        # Base: solo productos activos ordenados alfabéticamente
        qs = Product.objects.filter(is_active=True).order_by("name")

        # Parámetros de búsqueda desde la URL
        q = self.request.query_params.get("q")  # texto de búsqueda
        ptype = self.request.query_params.get("product_type")  # FRUTA o VERDURA

        # Filtrar por tipo si es válido
        if ptype in ("FRUTA", "VERDURA"):
            qs = qs.filter(product_type=ptype)

        # Filtrar por nombre (búsqueda parcial, sin distinguir mayúsculas)
        if q:
            qs = qs.filter(name__icontains=q)

        return qs


