
from django.urls import path
from . import views




urlpatterns = [
    
    path("send-test-email/", views.send_test_email, name="send_test_email"),
    
    
    path('admin/orders/', views.orders_list, name='admin_orders'),
    path('admin/orders/<int:order_id>/', views.order_detail_admin, name='admin_order_detail'),
    path('', views.index, name='index'),
    path('products/', views.products, name='products'),
    path('product/<int:id>/', views.product_detail, name='product_detail'),

    # CART
    path('add-to-cart/<int:product_id>/', views.add_to_cart, name='add_to_cart'),
    path('cart/', views.cart, name='cart'),
    path('remove-from-cart/<int:product_id>/', views.remove_from_cart, name='remove_from_cart'),
    path('clear-cart/', views.clear_cart, name='clear_cart'),

    # CHECKOUT / ORDERS
    path('checkout/', views.checkout, name='checkout'),
    
    path("order-confirmation/<int:order_id>/", views.order_confirmation, name="order_confirmation"),

    # AUTH / OTHER
    path('login/', views.login_view, name='login'),
    path('offers/', views.offers, name='offers'),

]

