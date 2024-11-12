from django.urls import path
from .views import *
from django.contrib.auth import views as auth_views
urlpatterns = [
    path('',dashboard, name='dashboard'),
    path('add/', add_customer, name='add_customer'),
    # path('pay_fees/', pay_fees, name='pay_fees'),
    path('login/', login_view, name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('fees/', fee_details, name='feeDetails'),
    path('pay_fees/<int:customer_id>/',pay_fees, name = "pay_fees"),
    path('profile/<int:customer_id>/', profile_view, name='profile'),
    path('edit/<int:customer_id>/', edit_customer, name='edit_customer'),
    path('customer/<int:customer_id>/fees/', customer_fee_details, name='customer_fee_details'),
    path('search_customer/', dedicated, name='dedicated'),
    path('get_fees/<int:id>/', get_fees, name='get_fees'),

]
