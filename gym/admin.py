from django.contrib import admin
from .models import Customer, FeeDetail, CategoryTable

class CustomerAdmin(admin.ModelAdmin):
    list_display = ('name', 'gender', 'blood_group', 'height', 'weight', 'bmi','admission_number', 'date_of_admission', 'is_active', 'months_remaining','email','phone_no','date_of_birth') 
    search_fields = ('name', 'admission_number', 'date_of_admission')
    readonly_fields = ('admission_number', 'bmi', 'months_remaining')

class FeeDetailAdmin(admin.ModelAdmin):
    list_display = ('customer', 'amount_paid', 'date_of_payment', 'month','year')
    search_fields = ('customer__name', 'date_of_payment')
    list_filter = ('date_of_payment', 'month')

class CategoryTableAdmin(admin.ModelAdmin):
    list_display = ('name', 'price')


admin.site.register(Customer, CustomerAdmin)
admin.site.register(FeeDetail, FeeDetailAdmin)
admin.site.register(CategoryTable, CategoryTableAdmin)

