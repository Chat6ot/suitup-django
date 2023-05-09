from django.urls import path
from . import views

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("register/", views.register, name="register"),
    path("login/", views.login, name="login"),
    path("logout/", views.logout, name="logout"),
    path("profile/", views.dashboard, name="dashboard"),
    path("orders/", views.user_orders, name="user_orders"),
    path("order_detail/<int:order_id>/", views.order_detail, name="order_detail"),
    path("change_password/", views.change_password, name="change_password"),

    path("activate/<uidb64>/<token>/", views.activate, name="activate"),
    path("forgotPassword/", views.forgot_password, name="forgot_password"),
    path("forgot_password_validate/<uidb64>/<token>/", views.forgot_password_validate, name="forgot_password_validate"),
    path("resetPassword/", views.reset_password, name="reset_password"),
]