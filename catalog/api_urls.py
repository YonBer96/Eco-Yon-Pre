from django.urls import path
from .api_views import ProductListView

urlpatterns = [
    path("products/", ProductListView.as_view()),
]
