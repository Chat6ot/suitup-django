from django import forms
from .models import Order


class OrderForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ["recipient_name", "phone", "address_line", "district", "city", "payment_method", "order_note"]
