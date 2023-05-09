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
            data = Order()
            data.user = current_user
            data.email = current_user.email
            data.recipient_name = form.cleaned_data["recipient_name"]
            data.phone = form.cleaned_data["phone"]
            data.address_line = form.cleaned_data["address_line"]
            data.district = form.cleaned_data["district"]
            data.city = form.cleaned_data["city"]
            data.payment_method = form.cleaned_data["payment_method"]
            data.order_note = form.cleaned_data["order_note"]
            data.order_total = grand_total
            data.delivery_fee = delivery_fee
            data.ip = request.META.get("REMOTE_ADDR")
            data.is_ordered = True
            data.save()

            # Generate order number
            yr = int(datetime.date.today().strftime("%Y"))
            dt = int(datetime.date.today().strftime("%d"))
            mt = int(datetime.date.today().strftime("%m"))
            d = datetime.date(yr, mt, dt)
            current_date = d.strftime("%Y%m%d")
            order_number = current_date + str(data.id)
            data.order_number = order_number
            data.save()

            order = Order.objects.get(user=current_user, order_number=order_number)

            for item in cart_items:
                order_product = OrderProduct()
                order_product.order_id = order.id
                order_product.user_id = current_user.id
                order_product.product_id = item.product_id
                order_product.quantity = item.quantity
                order_product.product_price = item.product.price
                order_product.ordered = True
                order_product.save()

                cart_item = CartItem.objects.get(id=item.id)
                product_variation = cart_item.variations.all()
                order_product = OrderProduct.objects.get(id=order_product.id)
                order_product.variations.set(product_variation)
                order_product.save()

                product = Product.objects.get(id=item.product_id)
                product.stock -= item.quantity
                product.save()

            CartItem.objects.filter(user=current_user).delete()

            mail_subject = "Thank you for your order!"
            message = render_to_string("orders/order_received_email.html", {
                "user": current_user,
                "order": order,
            })
            to_email = current_user.email
            send_email = EmailMessage(mail_subject, message, to=[to_email])
            send_email.send()

            order_products = OrderProduct.objects.filter(order_id=data.id)

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
