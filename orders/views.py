from django.shortcuts import render, redirect
from carts.models import CartItem
from .forms import OrderForm
from .models import Order, OrderProduct
from store.models import Product
import datetime
from django.core.mail import EmailMessage
from django.core import serializers
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
        if form.is_valid():
            # Store all the billing information inside Order table
            data = form.cleaned_data
            order = Order.objects.create(
                user=current_user,
                email=current_user.email,
                recipient_name=data["recipient_name"],
                phone=data["phone"],
                address_line=data["address_line"],
                district=data["district"],
                city=data["city"],
                payment_method=data["payment_method"],
                order_note=data["order_note"],
                order_total=grand_total,
                delivery_fee=delivery_fee,
                ip=request.META.get("REMOTE_ADDR"),
                is_ordered=True
            )

            # Generate order number
            current_date = datetime.date.today().strftime("%Y%m%d")
            order_number = current_date + str(order.id)
            order.order_number = order_number
            order.save()

            for item in cart_items:
                order_product = OrderProduct.objects.create(
                    order=order,
                    user=current_user,
                    product=item.product,
                    quantity=item.quantity,
                    product_price=item.product.price,
                    ordered=True
                )

                product_variation = item.variations.all()
                order_product.variations.set(product_variation)
                order_product.save()

                product = Product.objects.get(id=item.product_id)
                product.stock -= item.quantity
                product.save()

            cart_items.delete()

            mail_subject = "Thank you for your order!"
            message = render_to_string("orders/order_received_email.html", {
                "user": current_user,
                "order": order,
            })
            to_email = current_user.email
            send_email = EmailMessage(mail_subject, message, to=[to_email])
            send_email.send()

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
