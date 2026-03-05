from django import forms
from catalog.models import Product


class ProductCreateForm(forms.ModelForm):
    """
    Formulario HTML para crear y editar productos desde el dashboard.

    Se basa directamente en el modelo Product y se usa en vistas
    del panel de encargado para gestionar el catálogo.
    """

    class Meta:
        # Modelo del que se construye el formulario
        model = Product

        # Campos del modelo que se mostrarán en el formulario
        fields = [
            "name",
            "product_type",
            "description",
            "image",
            "price",
            "unit",
            "stock",
            "is_active",
        ]

        # Personalización de widgets HTML
        widgets = {
            # Textarea más grande para la descripción
            "description": forms.Textarea(attrs={
                "rows": 4,
                "placeholder": "Descripción del producto…"
            }),
        }
