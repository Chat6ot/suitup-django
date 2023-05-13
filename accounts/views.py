from django.shortcuts import render, redirect, get_object_or_404
from .forms import SignUpForm, UserForm, UserAddressForm
from .models import Account, UserAddress
from orders.models import Order, OrderProduct
from carts.views import Cart, _cart_id, CartItem
from django.contrib import messages, auth
from django.contrib.auth.decorators import login_required
import requests

# Verification email
from django.contrib.sites.shortcuts import get_current_site
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import EmailMessage


def register(request):
    if request.method == "POST":
        form = SignUpForm(request.POST)
        if form.is_valid():
            first_name = form.cleaned_data["first_name"]
            last_name = form.cleaned_data["last_name"]
            email = form.cleaned_data["email"]
            password = form.cleaned_data["password"]
            phone_number = form.cleaned_data["phone_number"]
            username = first_name + " " + last_name

            user = Account.objects.create_user(first_name=first_name,
                                               last_name=last_name,
                                               email=email,
                                               password=password,
                                               username=username)

            user.phone_number = phone_number
            user.save()

            # Create User Address
            address = UserAddress()
            address.user_id = user.id
            address.save()

            # USER ACTIVATION
            current_site = get_current_site(request)
            mail_subject = "Please activate your account."
            message = render_to_string("accounts/account_verification_email.html", {
                "user": user,
                "domain": current_site,
                "uid": urlsafe_base64_encode(force_bytes(user.pk)),
                "token": default_token_generator.make_token(user)
            })
            to_email = email
            send_email = EmailMessage(mail_subject, message, to=[to_email])
            send_email.send()

            messages.success(request,
                             "Please activate your account. "
                             "We have sent you a verification email to your email address.")
            return redirect("login")
    else:
        form = SignUpForm()

    context = {
        "form": form,
    }

    return render(request, "accounts/register.html", context)


def login(request):
    if request.method == "POST":
        email = request.POST["email"]
        password = request.POST["password"]

        user = auth.authenticate(email=email, password=password)

        if user:
            try:
                cart = Cart.objects.get(cart_id=_cart_id(request))
                cart_item_exists = CartItem.objects.filter(cart=cart).exists()
                if cart_item_exists:

                    # Get the product variations by cart id
                    cart_items_by_id = CartItem.objects.filter(cart=cart)
                    variations_by_id = []
                    for item in cart_items_by_id:
                        variation = item.variations.all()
                        variations_by_id.append(list(variation))

                    # Get the cart items from the user to access his product variations
                    cart_items_by_user = CartItem.objects.filter(user=user)
                    ids = [item.id for item in cart_items_by_user]

                    variations_by_cart = []
                    for item in cart_items_by_user:
                        variation = item.variations.all()
                        variations_by_cart.append(list(variation))

                    for variation_id in variations_by_id:
                        if variation_id in variations_by_cart:
                            index = variations_by_cart.index(variation_id)
                            item_id = ids[index]
                            item = CartItem.objects.get(id=item_id)
                            item.quantity += 1
                            item.user = user
                            item.save()

                    for item in cart_items_by_id:
                        if item.user != user:
                            item.user = user
                            item.save()
            except:
                pass

            auth.login(request, user)
            url = request.META.get('HTTP_REFERER')
            try:
                query = requests.utils.urlparse(url).query
                params = dict(x.split("=") for x in query.split("&"))
                if "next" in params:
                    nextPage = params["next"]
                    return redirect(nextPage)
            except:
                return redirect("home")
        else:
            messages.error(request, "Invalid login credentials")
            return redirect("login")

    return render(request, "accounts/login.html")


@login_required(login_url="login")
def logout(request):
    auth.logout(request)
    return redirect("login")


def activate(request, uidb64, token):
    try:
        uid = urlsafe_base64_decode(uidb64).decode()
        user = Account._default_manager.get(pk=uid)
    except(TypeError, ValueError, OverflowError, Account.DoesNotExist):
        user = None

    if user and default_token_generator.check_token(user, token):
        user.is_active = True
        user.save()
        messages.success(request, "Your account is activated.")
        return redirect("login")
    else:
        messages.error(request, "Invalid activation link.")
        return redirect("register")


@login_required(login_url="login")
def dashboard(request):
    user = request.user
    user_address = get_object_or_404(UserAddress, user=user)

    if request.method == "POST":
        user_form = UserForm(request.POST, instance=user)
        user_address_form = UserAddressForm(request.POST, instance=user_address)
        if user_form.is_valid():
            user_form.save()

            if user_address_form.is_valid():
                user_address_form.save()

            messages.success(request, "Your profile has been updated.")
            return redirect("dashboard")
    else:
        user_form = UserForm(instance=user)
        user_address_form = UserAddressForm(instance=user_address)

    context = {
        "user": user,
        "user_form": user_form,
        "user_address_form": user_address_form,
    }

    return render(request, "accounts/dashboard.html", context)


@login_required(login_url="login")
def change_password(request):
    if request.method == "POST":
        current_password = request.POST["current_password"]
        new_password = request.POST["new_password"]
        confirm_password = request.POST["confirm_password"]

        user = Account.objects.get(username__exact=request.user.username)

        if new_password == confirm_password:
            success = user.check_password(current_password)
            if success:
                user.set_password(new_password)
                user.save()
                messages.success(request, "Password updated successfully.")
                return redirect("dashboard")
            else:
                messages.error(request, "Please enter valid current password.")
        else:
            messages.error(request, "Password does not match!")
        return redirect("change_password")
    return render(request, "accounts/change_password.html")


@login_required(login_url="login")
def user_orders(request):
    current_user = request.user

    orders = Order.objects.filter(user=current_user, is_ordered=True).order_by("-created_at")

    context = {
        "orders": orders,
    }

    return render(request, "accounts/user_orders.html", context)


@login_required(login_url="login")
def order_detail(request, order_id):
    order_detail = OrderProduct.objects.filter(order__order_number=order_id)
    order = Order.objects.get(order_number=order_id)

    subtotal = 0
    quantity = 0
    for i in order_detail:
        subtotal += i.product.price * i.quantity
        quantity += i.quantity

    context = {
        "order_detail": order_detail,
        "order": order,
        "subtotal": subtotal,
        "quantity": quantity,
    }

    return render(request, "accounts/order_detail.html", context)


def forgot_password(request):
    if request.method == "POST":
        email = request.POST["email"]
        if Account.objects.filter(email=email).exists():
            user = Account.objects.get(email__exact=email)

            # Reset password email
            current_site = get_current_site(request)
            mail_subject = "Reset Your Password"
            message = render_to_string("accounts/reset_password_email.html", {
                "user": user,
                "domain": current_site,
                "uid": urlsafe_base64_encode(force_bytes(user.pk)),
                "token": default_token_generator.make_token(user)
            })
            to_email = email
            send_email = EmailMessage(mail_subject, message, to=[to_email])
            send_email.send()

            messages.success(request, "Password reset email has been sent to your email address.")
            return redirect("login")

        else:
            messages.error(request, "Account does not exist!")
            return redirect("forgot_password")
    return render(request, "accounts/forgot_password.html")


def forgot_password_validate(request, uidb64, token):
    uid = None

    try:
        uid = urlsafe_base64_decode(uidb64).decode()
        user = Account._default_manager.get(pk=uid)
    except(TypeError, ValueError, OverflowError, Account.DoesNotExist):
        user = None

    if user and default_token_generator.check_token(user, token):
        request.session["uid"] = uid
        messages.success(request, "Please reset your password.")
        return redirect("reset_password")
    else:
        messages.error(request, "This link is has been expired!")
        return redirect("login")


def reset_password(request):
    if request.method == "POST":
        password = request.POST["password"]
        confirm_password = request.POST["confirm_password"]
        if password == confirm_password:
            uid = request.session.get("uid")
            user = Account.objects.get(pk=uid)
            user.set_password(password)
            user.save()
            messages.success(request, "Password reset successful.")
            return redirect("login")
        else:
            messages.error(request, "Password does not match.")
            return redirect("reset_password")
    else:
        return render(request, "accounts/reset_password.html")