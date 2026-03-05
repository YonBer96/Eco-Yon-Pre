from rest_framework import serializers
from .models import Product


class ProductSerializer(serializers.ModelSerializer):
    """
    Serializer de lectura para el modelo Product.

    Se encarga de convertir objetos Product en JSON para la API,
    definiendo exactamente qué campos se exponen al frontend y
    cómo se construyen (por ejemplo, la URL completa de la imagen).
    """

    # Campo calculado: no se envía directamente desde el modelo,
    # sino que se genera con el método get_image()
    image = serializers.SerializerMethodField()

    # clase de conf para que ModelSerilizer comunique correctamente que quiere enviar al front
    class Meta:
        # Modelo sobre el que se basa este serializer
        model = Product

        # Campos que se enviarán al frontend en formato JSON
        fields = (
            "id",            # Identificador del producto
            "name",          # Nombre del producto
            "product_type",  # Tipo (FRUTA / VERDURA)
            "description",   # Descripción del producto
            "price",         # Precio por unidad
            "unit",          # Unidad de venta (kg, unidad, etc.)
            "stock",         # Stock disponible
            "image",         # URL completa de la imagen
        )

    def get_image(self, obj):
        """
        Devuelve la URL de la imagen del producto.

        Si hay un request disponible en el contexto, construye
        una URL absoluta (ej: http://127.0.0.1:8000/media/...)
        para que el frontend pueda consumirla directamente.

        Si no hay imagen, devuelve None.
        """

        # Intentamos obtener el request que DRF pasa al serializer
        request = self.context.get("request")

        # Comprobamos que el producto tiene imagen y que Django le asignó una URL
        if obj.image and hasattr(obj.image, "url"):

            # Si tenemos request, devolvemos la URL absoluta
            if request:
                return request.build_absolute_uri(obj.image.url)

            # Si no hay request, devolvemos la URL relativa
            return obj.image.url

        # Si no hay imagen, devolvemos null en el JSON
        return None

