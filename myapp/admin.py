from django.contrib import admin
from .models import Product
from django.contrib import admin
from .models import Order, OrderItem


from .models import Product, Order, OrderItem


admin.site.register(Product)



class OrderItemInline(admin.TabularInline):
    model = OrderItem
    readonly_fields = ('product', 'quantity', 'price')
    extra = 0

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'full_name', 'phone', 'total_price', 'status', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('full_name', 'phone', 'id')
    inlines = [OrderItemInline]


# @admin.register(Order)
# class OrderAdmin(admin.ModelAdmin):
#     list_display = ('id', 'full_name', 'phone', 'total_price', 'status' if hasattr(Order, 'status') else 'id')
#     search_fields = ('full_name','phone','address')
#     list_filter = ('created_at',) if hasattr(Order, 'created_at') else ()
#     readonly_fields = ('id',)

@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ('id','order','product','quantity','price')
    search_fields = ('order__id','product__name')
