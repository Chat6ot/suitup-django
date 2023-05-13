from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponseRedirect
from django.core.exceptions import ObjectDoesNotExist
from store.models import Product, Variation
from .models import Cart, CartItem
from django.contrib.auth.decorators import login_required


def _cart_id(request):
    cart = request.session.session_key
    if not cart:
        cart = request.session.create()
    return cart


def _create_cart_item(product, quantity, user, cart, variations):
    if user:
        cart_item = CartItem.objects.create(product=product, quantity=quantity, user=user)
    else:
        cart_item = CartItem.objects.create(product=product, quantity=quantity, cart=cart)
    if variations:
        cart_item.variations.add(*variations)
    cart_item.save()


def add_to_cart(request, product_id):
    current_user = request.user if request.user.is_authenticated else None
    cart = None
    order_quantity = None
    add_to_cart = None

    product = Product.objects.get(id=product_id)

    product_variation = []
    if request.method == 'POST':
        order_quantity = int(request.POST.get("quantity", 1))
        add_to_cart = request.POST.get('add_to_cart', False)
        for key, value in request.POST.items():
            try:
                variation = Variation.objects.get(product=product,
                                                  variation_category__iexact=key,
                                                  variation_value__iexact=value)
                product_variation.append(variation)
            except Variation.DoesNotExist:
                pass

    if current_user:
        cart_items = CartItem.objects.filter(product=product, user=current_user)
    else:
        try:
            cart = Cart.objects.get(cart_id=_cart_id(request))
        except Cart.DoesNotExist:
            cart = Cart.objects.create(cart_id=_cart_id(request))
            cart.save()
        cart_items = CartItem.objects.filter(product=product, cart=cart)

    if cart_items.exists():
        ex_var_list = []
        ids = []

        for item in cart_items:
            ids.append(item.id)
            existing_variation = item.variations.all()
            ex_var_list.append(list(existing_variation))

        if product_variation in ex_var_list:
            index = ex_var_list.index(product_variation)
            item_id = ids[index]
            item = CartItem.objects.get(product=product, id=item_id)
            item.quantity += order_quantity
            item.save()
        else:
            _create_cart_item(
                product=product,
                quantity=order_quantity,
                user=current_user,
                cart=cart,
                variations=product_variation,
            )
    else:
        _create_cart_item(
            product=product,
            quantity=order_quantity,
            user=current_user,
            cart=cart,
            variations=product_variation,
        )

    if add_to_cart:
        return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
    return redirect("cart")


def decrease_cart(request, product_id, cart_item_id):
    current_user = request.user
    product = get_object_or_404(Product, id=product_id)

    try:
        if current_user.is_authenticated:
            cart_item = CartItem.objects.get(product=product, user=current_user, id=cart_item_id)
        else:
            cart = Cart.objects.get(cart_id=_cart_id(request))
            cart_item = CartItem.objects.get(product=product, cart=cart, id=cart_item_id)
        if cart_item.quantity > 1:
            cart_item.quantity -= 1
            cart_item.save()
        else:
            cart_item.delete()
    except:
        pass
    return redirect("cart")


def remove_cart(request, product_id, cart_item_id):
    product = get_object_or_404(Product, id=product_id)
    if request.user.is_authenticated:
        cart_item = CartItem.objects.get(product=product, user=request.user, id=cart_item_id)
    else:
        cart = Cart.objects.get(cart_id=_cart_id(request))
        cart_item = CartItem.objects.get(product=product, cart=cart, id=cart_item_id)

    cart_item.delete()
    return redirect("cart")


def cart(request, total=0, quantity=0, cart_items=None):
    delivery_fee = 100
    grand_total = 0

    try:
        if request.user.is_authenticated:
            cart_items = CartItem.objects.filter(user=request.user, is_active=True)
        else:
            cart = Cart.objects.get(cart_id=_cart_id(request))
            cart_items = CartItem.objects.filter(cart=cart, is_active=True)

        for cart_item in cart_items:
            total += (cart_item.product.price * cart_item.quantity)
            quantity += cart_item.quantity
        grand_total = total + delivery_fee
    except ObjectDoesNotExist:
        pass

    context = {
        "delivery_fee": delivery_fee,
        "total": total,
        "quantity": quantity,
        "cart_items": cart_items,
        "grand_total": grand_total,
    }

    return render(request, "store/cart.html", context)


@login_required(login_url="login")
def checkout(request, total=0, quantity=0, cart_items=None):
    delivery_fee = 100
    grand_total = 0

    try:
        cart_items = CartItem.objects.filter(user=request.user, is_active=True)
        for cart_item in cart_items:
            total += (cart_item.product.price * cart_item.quantity)
            quantity += cart_item.quantity
        grand_total = total + delivery_fee

        if grand_total == delivery_fee:
            return redirect("cart")

    except ObjectDoesNotExist:
        pass

    context = {
        "delivery_fee": delivery_fee,
        "total": total,
        "quantity": quantity,
        "cart_items": cart_items,
        "grand_total": grand_total,
    }

    return render(request, "store/checkout.html", context)
