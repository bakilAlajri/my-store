from django.shortcuts import render, redirect, get_object_or_404
from django.db import transaction
from django.urls import reverse
from django.http import HttpResponse
from django.conf import settings
from django.contrib.admin.views.decorators import staff_member_required

from django.core.mail import send_mail, EmailMultiAlternatives
from django.template.loader import render_to_string

from urllib.parse import quote_plus

from .models import Product, Order, OrderItem

# ===============================
# الصفحة الرئيسية
# ===============================
def index(request):
    products = Product.objects.all()[:8]
    return render(request, 'myapp/index.html', {'products': products})

def products(request):
    products = Product.objects.all()
    return render(request, 'myapp/products.html', {'products': products})

def product_detail(request, id):
    product = get_object_or_404(Product, id=id)
    return render(request, 'myapp/product-detail.html', {'product': product})


# ===============================
# صفحة الدفع Checkout
# ===============================
def checkout(request):
    cart = request.session.get("cart", {})
    cart_items = []
    total_price = 0

    for product_id, quantity in cart.items():
        product = get_object_or_404(Product, id=int(product_id))
        total = product.price * quantity
        total_price += total
        cart_items.append({
            "product": product,
            "quantity": quantity,
            "total": total,
        })

    if request.method == "POST":
        full_name = request.POST.get("full_name", "").strip()
        address = request.POST.get("address", "").strip()
        phone = request.POST.get("phone", "").strip()
        email = request.POST.get("email", "").strip()

        if not full_name or not address or not phone or not email:
            return render(request, "myapp/checkout.html", {
                "cart_items": cart_items,
                "total_price": total_price,
                "error": "الرجاء ملء جميع الحقول المطلوبة."
            })

        # حفظ الطلب
        with transaction.atomic():
            order = Order.objects.create(
                full_name=full_name,
                address=address,
                phone=phone,
                total_price=total_price
            )

            for item in cart_items:
                OrderItem.objects.create(
                    order=order,
                    product=item["product"],
                    quantity=item["quantity"],
                    price=item["product"].price
                )

        # ==============================================================
        # 1) 📧 إرسال بريد HTML لصاحب المتجر
        # ==============================================================

        store_email = getattr(settings, "STORE_EMAIL", "bikaylalejri2024@gmail.com")

        subject_admin = f"طلب جديد رقم {order.id}"

        # HTML template لصاحب المتجر
        # ملاحظة: ملف القالب موجود بمسار: myapp/templates/myapp/emails/admin_order.html
        html_admin = render_to_string("myapp/emails/admin_order.html", {
            "order": order,
            "cart_items": cart_items,
            "total_price": total_price,
            "full_name": full_name,
            "phone": phone,
            "address": address,
        })

        text_admin = f"وصل طلب جديد من {full_name} — إجمالي: {total_price} ريال"

        email_admin = EmailMultiAlternatives(
            subject_admin,
            text_admin,
            settings.EMAIL_HOST_USER,
            [store_email],
        )
        email_admin.attach_alternative(html_admin, "text/html")
        email_admin.send()

        # ==============================================================
        # 2) 📧 إرسال بريد HTML للعميل
        # ==============================================================

        subject_user = "تأكيد طلبك"

        # ملاحظة: قالب المستخدم موجود بمسار: myapp/templates/myapp/emails/user_order.html
        html_user = render_to_string("myapp/emails/user_order.html", {
            "order": order,
            "cart_items": cart_items,
            "total_price": total_price,
            "full_name": full_name,
        })

        text_user = "شكراً لطلبك من متجرنا!"

        msg_user = EmailMultiAlternatives(
            subject_user,
            text_user,
            settings.EMAIL_HOST_USER,
            [email],
        )
        msg_user.attach_alternative(html_user, "text/html")
        msg_user.send()

        # ==============================================================
        # 3) 🔔 توليد روابط واتساب جاهزة (مجانية) ووضعها في session
        #     (لا ترسل تلقائياً — بل تضع الرابط ليجري فتحه من العميل أو المشرف)
        # ==============================================================

        # تنظيف رقم العميل إلى صيغة دولية بدون علامة +
        def clean_phone(p):
            if not p:
                return ""
            # احذف المسافات والأقواس والشرطات والبواقي
            cleaned = p.replace("+", "").replace(" ", "").replace("-", "").replace("(", "").replace(")", "")
            return cleaned

        customer_phone = clean_phone(phone)
        # رسالة العميل (ستظهر جاهزة داخل واتساب العميل)
        customer_msg = f"مرحبًا {full_name}، تم استلام طلبك رقم {order.id} وإجمالي المبلغ {total_price} ريال. شكراً لتسوقك معنا!"
        customer_whatsapp_link = None
        if customer_phone:
            customer_whatsapp_link = f"https://wa.me/{customer_phone}?text={quote_plus(customer_msg)}"

        # رسالة لمالك المتجر/المشرف (اختياري — سيحفظ الرابط في الجلسة)
        store_phone = getattr(settings, "STORE_WHATSAPP_NUMBER", None)  # ضع رقمك في settings.py إن أردت إشعارات واتساب للمتجر
        owner_whatsapp_link = None
        if store_phone:
            store_phone_clean = clean_phone(store_phone)
            owner_msg = f"📦 طلب جديد #{order.id}\nالاسم: {full_name}\nالهاتف: {phone}\nالإجمالي: {total_price} ر.س"
            owner_whatsapp_link = f"https://wa.me/{store_phone_clean}?text={quote_plus(owner_msg)}"

        # خزّن الروابط في الجلسة لتظهر في صفحة تأكيد الطلب
        request.session['last_order_whatsapp'] = customer_whatsapp_link
        request.session['last_order_owner_whatsapp'] = owner_whatsapp_link
        # (يمكنك لاحقاً إظهار زر في order-confirmation.html يستخدم هذه الجلسة لفتح واتساب)

        # تفريغ السلة
        request.session["cart"] = {}

        # إعادة توجيه لصفحة تأكيد الطلب (التي يمكنها عرض رابط واتساب المحفوظ في الجلسة)
        return redirect(reverse("order_confirmation", kwargs={"order_id": order.id}))

    return render(request, "myapp/checkout.html", {
        "cart_items": cart_items,
        "total_price": total_price
    })


def order_confirmation(request, order_id):
    order = Order.objects.get(id=order_id)

    return render(request, "myapp/order-confirmation.html", {
        "order_id": order_id,
        "customer_phone": order.phone.replace(" ", ""),
        "customer_name": order.full_name,
    })


def login_view(request):
    return render(request, 'myapp/login.html')


def offers(request):
    return render(request, 'myapp/offers.html')


# ===============================
# السلة
# ===============================
def add_to_cart(request, product_id):
    cart = request.session.get('cart', {})
    product_id = str(product_id)
    cart[product_id] = cart.get(product_id, 0) + 1
    request.session['cart'] = cart
    return redirect('cart')


def cart(request):
    cart = request.session.get('cart', {})
    cart_items = []
    total_price = 0

    for product_id, qty in cart.items():
        product = get_object_or_404(Product, id=product_id)
        item_total = product.price * qty
        total_price += item_total

        cart_items.append({
            'product': product,
            'quantity': qty,
            'total': item_total
        })

    return render(request, 'myapp/cart.html', {
        'cart_items': cart_items,
        'total_price': total_price
    })


def remove_from_cart(request, product_id):
    cart = request.session.get('cart', {})
    product_id = str(product_id)

    if product_id in cart:
        del cart[product_id]

    request.session['cart'] = cart
    return redirect('cart')


def clear_cart(request):
    request.session['cart'] = {}
    return redirect('cart')


def send_test_email(request):
    send_mail(
        subject="اختبار الإيميل",
        message="هذه رسالة اختبارية للتأكد من أن الإرسال يعمل 100%",
        from_email=settings.EMAIL_HOST_USER,
        recipient_list=[getattr(settings, "STORE_EMAIL", "bikaylalejri2024@gmail.com")],
        fail_silently=False,
    )
    return HttpResponse("تم إرسال الإيميل بنجاح ✔️")


# ===============================
# إدارة الطلبات للمشرف
# ===============================
@staff_member_required
def orders_list(request):
    orders = Order.objects.all().order_by('-id')
    return render(request, "myapp/admin/orders_list.html", {"orders": orders})


@staff_member_required
def order_detail_admin(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    items = OrderItem.objects.filter(order=order)
    return render(request, "myapp/admin/order_detail.html", {
        "order": order,
        "items": items
    })
