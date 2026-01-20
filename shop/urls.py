from django.urls import path
from . import views

urlpatterns = [
    path("add-to-cart/<int:product_id>/", views.add_to_cart, name="add_to_cart"),
    path("", views.home, name="home"),
    path("category/<int:category_id>/", views.category, name="category"),
    path("product/<int:product_id>/", views.product, name="product"),
    path('orders/add/<int:product_id>/', views.add_to_cart, name='add_to_cart'),
]
