from django.shortcuts import render
from store.models import Product


def home(request):
    products = Product.objects.all().filter(is_available=True).order_by("stock")
    top_products = list(products[:8])

    context = {
        "top_products": top_products,
    }

    return render(request, "index.html", context)
