from django.db import models
from django.utils import timezone
from django.core.exceptions import ValidationError
class CategoryTable(models.Model):
    name = models.CharField(max_length=50)
    price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return self.name
class Customer(models.Model):
    GENDER_CHOICES = [
        ('M', 'Male'),
        ('F', 'Female'),
    ]

    BLOOD_GROUP_CHOICES = [
        ('O+', 'O+'),
        ('O-', 'O-'),
        ('A+', 'A+'),
        ('A-', 'A-'),
        ('B+', 'B+'),
        ('B-', 'B-'),
        ('AB+', 'AB+'),
        ('AB-', 'AB-'),
        ('A1+', 'A1+'),
        ('A1-', 'A1-'),
        ('A2+', 'A2+'),
        ('A2-', 'A2-'),
        ('A1B+', 'A1B+'),
        ('A1B-', 'A1B-'),
        ('A2B+', 'A2B+'),
        ('A2B-', 'A2B-'),
        ('BOMBAY', 'BOMBAY'),
    ]





    unique_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255,blank=False)
    phone_no = models.CharField(max_length=10, blank=True)
    email = models.EmailField(null=True, blank=True)
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES,blank=False)
    height = models.FloatField(help_text='Height in centimeters', null=True, blank=True)
    weight = models.FloatField(help_text='Weight in kilograms', null=True, blank=True)
    blood_group = models.CharField(max_length=6, choices=BLOOD_GROUP_CHOICES,blank=False)
    bmi = models.FloatField(editable=False, null=True, blank=True)
    admission_number = models.PositiveIntegerField(editable=False, default=0)
    date_of_admission = models.DateField(default=timezone.now)
    date_of_birth = models.DateField(null=True, blank=True)
    class Meta:
        unique_together = ('name', 'phone_no')
    @property
    def is_active(self):
        current_year = timezone.now().year
        current_month = timezone.now().month
        fees_paid = self.feedetail_set.filter(date_of_payment__year=current_year).values_list('month', flat=True)
        return current_month in fees_paid

    @property
    def months_remaining(self):
        current_year = timezone.now().year
        current_month = timezone.now().month
        fees_paid = self.feedetail_set.filter(date_of_payment__year=current_year).values_list('month', flat=True)
        remaining_months = len([month for month in range(current_month, 13) if month not in fees_paid])
        return remaining_months 

    def save(self, *args, **kwargs):
        if not self.admission_number:
            last_customer = Customer.objects.filter(gender=self.gender).order_by('admission_number').last()
            print(last_customer)
            if last_customer:
                self.admission_number = last_customer.admission_number + 1
            else:
                self.admission_number = 10000
        if self.height and self.weight:
            self.bmi = round(self.weight / (self.height / 100) ** 2, 2)
        super().save(*args, **kwargs)


    def __str__(self):
        return self.name


class FeeDetail(models.Model):
    MONTH_CHOICES = [
        (1, 'January'),
        (2, 'February'),
        (3, 'March'),
        (4, 'April'),
        (5, 'May'),
        (6, 'June'),
        (7, 'July'),
        (8, 'August'),
        (9, 'September'),
        (10, 'October'),
        (11, 'November'),
        (12, 'December'),
    ]

    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2)
    date_of_payment = models.DateField(default=timezone.now)
    category = models.ForeignKey(CategoryTable,on_delete=models.PROTECT)
    month = models.PositiveSmallIntegerField(choices=MONTH_CHOICES, default=timezone.now().month)
    year = models.IntegerField(default=timezone.now().year)
    #unique together month year and category
    class Meta:
        unique_together = ('month', 'year',
                            'category', 'customer')
        
    def delete(self, *args, **kwargs):
        # Prevent deletion if the category name is 'Fees'
        if self.name == 'Fees':
            raise ValidationError("Cannot delete the 'Fees' category.")
        super().delete(*args, **kwargs)
    def __str__(self):
        return f"{self.customer.name} - {self.get_month_display()} - {self.amount_paid}"
