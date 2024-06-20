from django.urls import path
from . import views
from .views import remove_from_cart


urlpatterns = [
    path('', views.dish_list, name='dish_list'),
    path('cart/', views.cart, name='cart'),
    path('cart/add/<int:product_id>/', views.add_to_cart, name='add_to_cart'),
    path('cart/update/', views.update_cart, name='update_cart'),
    path('cart/remove/', views.remove_from_cart, name='remove_from_cart'),
]

