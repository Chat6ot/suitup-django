from django.shortcuts import render, redirect
from carts.models import CartItem
from .forms import OrderForm
from .models import Order, OrderProduct
from store.models import Product
import datetime
from django.core.mail import EmailMessage
from django.template.loader import render_to_string


def place_order(request, total=0, quantity=0):
    current_user = request.user
    cart_items = CartItem.objects.filter(user=current_user, is_active=True)
    cart_count = cart_items.count()
    if not cart_count:
        return redirect("store")

    delivery_fee = 100

    for item in cart_items:
        total += (item.product.price * item.quantity)
        quantity += item.quantity

    grand_total = total + delivery_fee

    if request.method == "POST":
        form = OrderForm(request.POST)
        ip = request.META.get("REMOTE_ADDR")
        if form.is_valid():
            order = _create_order(form, current_user, grand_total, delivery_fee, ip)
            _create_order_product(order, current_user, cart_items)
            _update_product_stock(cart_items)
            _send_order_confirmation_mail(order, current_user)
            # clear cart items by user
            cart_items.delete()

            order_products = OrderProduct.objects.filter(order=order)

            context = {
                "order": order,
                "order_products": order_products,
                "quantity": quantity,
                "total": total,
                "delivery_fee": delivery_fee,
                "grand_total": grand_total
            }

            return render(request, "store/orders.html", context)
        else:
            print(form.errors)

    return redirect("checkout")


def _create_order(form, user, grand_total, delivery_fee, ip):
    data = form.cleaned_data
    order = Order.objects.create(
        user=user,
        email=user.email,
        recipient_name=data["recipient_name"],
        phone=data["phone"],
        address_line=data["address_line"],
        district=data["district"],
        city=data["city"],
        payment_method=data["payment_method"],
        order_note=data["order_note"],
        order_total=grand_total,
        delivery_fee=delivery_fee,
        ip=ip,
        is_ordered=True
    )
    current_date = datetime.date.today().strftime("%Y%m%d")
    order_number = current_date + str(order.id)
    order.order_number = order_number
    order.save()
    return order


def _create_order_product(order, user, cart_items):
    for item in cart_items:
        order_product = OrderProduct.objects.create(
            order=order,
            user=user,
            product=item.product,
            quantity=item.quantity,
            product_price=item.product.price,
            ordered=True
        )

        product_variation = item.variations.all()
        order_product.variations.set(product_variation)
        order_product.save()


def _update_product_stock(cart_items):
    for item in cart_items:
        product = Product.objects.get(id=item.product_id)
        product.stock -= item.quantity
        product.save()


def _send_order_confirmation_mail(order, user):
    mail_subject = "Thank you for your order!"
    message = render_to_string("orders/order_received_email.html", {
        "user": user,
        "order": order,
    })
    to_email = user.email
    send_email = EmailMessage(mail_subject, message, to=[to_email])
    send_email.send()
