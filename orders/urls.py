from django.urls import path
from . import views

urlpatterns = [
    # корзина
    path("add/<int:product_id>/", views.add_to_cart, name="add_to_cart"),
    path("remove/<int:product_id>/", views.remove_from_cart, name="remove_from_cart"),
    path("cart/", views.cart, name="cart"),
    path("checkout/", views.checkout, name="checkout"),
    path("success/<int:order_id>/", views.success, name="success"),

    # 👇 ВОТ ЭТО НОВОЕ
    path("track/", views.track_order, name="track_order"),
    path("order/<int:order_id>/", views.order_detail, name="order_detail"),
    path("cancel/<int:order_id>/", views.cancel_order, name="cancel_order"),
    path("t/<str:token>/", views.order_detail_token, name="order_detail_token"),
    path("t/<str:token>/cancel/", views.cancel_order_token, name="cancel_order_token"),
]
