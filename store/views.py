from django.shortcuts import render, get_object_or_404
from django.db.models import Q
from .models import Product, ProductGallery
from category.models import Category
from django.core.paginator import Paginator


def store(request, category_slug=None):
    categories = None
    products = None

    if category_slug:
        categories = get_object_or_404(Category, slug=category_slug)
        products = Product.objects.filter(category=categories, is_available=True)
        paginator = Paginator(products, 6)
        page = request.GET.get("page")
        paged_products = paginator.get_page(page)
    else:
        products = Product.objects.all().filter(is_available=True).order_by("id")
        paginator = Paginator(products, 9)
        page = request.GET.get("page")
        paged_products = paginator.get_page(page)

    product_count = products.count()

    context = {
        "products": paged_products,
        "categories": categories,
        "product_count": product_count,
    }

    return render(request, "store/store.html", context)


def product_detail(request, category_slug, product_slug):
    try:
        single_product = Product.objects.get(category__slug=category_slug, slug=product_slug)
    except Exception as e:
        raise e

    product_gallery = ProductGallery.objects.filter(product_id=single_product.id)

    context = {
        "single_product": single_product,
        "product_gallery": product_gallery,
    }

    return render(request, "store/product_detail.html", context)


def search(request):
    keyword = None
    products = None
    product_count = 0

    if "keyword" in request.GET:
        keyword = request.GET["keyword"]
        if keyword:
            products = Product.objects.order_by("-created_date").filter(
                Q(description__icontains=keyword) | Q(product_name__icontains=keyword))
            product_count = products.count()
            keyword = keyword

    context = {
        "products": products,
        "product_count": product_count,
        "keyword": keyword,
    }

    return render(request, "store/store.html", context)
