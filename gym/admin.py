from django.contrib import admin
from .models import Customer, FeeDetail, CategoryTable

class CustomerAdmin(admin.ModelAdmin):
    list_display = ('admission_number','name', 'gender', 'blood_group', 'height', 'weight', 'bmi', 'date_of_admission', 'email','phone_no','date_of_birth') 
    search_fields = ('admission_number','name',  'date_of_admission')
    readonly_fields = ('admission_number', 'bmi')

class FeeDetailAdmin(admin.ModelAdmin):
    list_display = ('customer', 'amount_paid', 'date_of_payment', 'month','year')
    search_fields = ('customer__name', 'date_of_payment')
    list_filter = ('date_of_payment', 'month')

class CategoryTableAdmin(admin.ModelAdmin):
    list_display = ('name', 'price','no_of_months','is_fees')


admin.site.register(Customer, CustomerAdmin)
admin.site.register(FeeDetail, FeeDetailAdmin)
admin.site.register(CategoryTable, CategoryTableAdmin)

