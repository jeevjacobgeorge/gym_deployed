
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from .models import Customer, FeeDetail, CategoryTable
# from .forms import CustomerForm, FeePaymentForm
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import AuthenticationForm
import datetime
from datetime import datetime, timedelta
from django.utils import timezone  # For timezone-aware operations
from django.db import models, IntegrityError
from django.db.models import Q, Prefetch, Count

@login_required
def dashboard(request):
    print("dashboard")
    data = {}

    # General stats
    data['no_of_customers'] = Customer.objects.count()
    data['no_of_male'] = Customer.objects.filter(gender='M').count()
    data['no_of_female'] = Customer.objects.filter(gender='F').count()

    # Calculate last 3 months (considering year transitions)
    current_date = datetime.now()
    last_3_months = [(current_date.month - i - 1) % 12 + 1 for i in range(3)]
    last_3_years = [current_date.year - (1 if current_date.month - i - 1 < 0 else 0) for i in range(3)]
    months_and_years = list(zip(last_3_months, last_3_years))

    # Pre-fetch necessary data
    fee_categories = CategoryTable.objects.filter(is_fees=True).values_list('id', flat=True)
    fee_details = FeeDetail.objects.filter(
        Q(month__in=[m[0] for m in months_and_years], year__in=[y[1] for y in months_and_years]),
        category_id__in=fee_categories
    ).select_related('customer')

    # Count active males and females
    active_customers = fee_details.values('customer__pk', 'customer__gender').distinct()
    active_male_count = active_customers.filter(customer__gender='M').count()
    active_female_count = active_customers.filter(customer__gender='F').count()

    # Populate active counts
    data['no_of_active_males'] = active_male_count
    data['no_of_active_females'] = active_female_count

    print("dashboard2")
    return render(request, 'gym/dashboard.html', data)



def logout_view(request):
    logout(request)
    return redirect('login')

@login_required
def add_customer(request):
    if request.method == 'POST':
        # Capture form data
        name = request.POST.get('name')
        phone = request.POST.get('phone')
        email = request.POST.get('email')
        gender = request.POST.get('gender')
        height = request.POST.get('height')
        weight = request.POST.get('weight')
        blood_group = request.POST.get('bloodGroup')
        date_of_admission = request.POST.get('date_of_admission')
        dob = request.POST.get('dob')
        admission_number = request.POST.get('admission_number')
        health = request.POST.get('health')

        # Handle empty fields for height and weight
        if height == '':
            height = None
        else:
            height = float(height)
        if weight == '':
            weight = None
        else:
            weight = float(weight)

        errors = []

        # Validate form data
        if not name:
            errors.append("Name is required.")
        if not phone or len(phone) != 10:
            errors.append("Valid phone number is required.")
        

        # Parse and validate dates
        try:
            if date_of_admission:
                date_of_admission = datetime.strptime(date_of_admission, '%Y-%m-%d').date()
            else:
                date_of_admission = None  # Handle empty date
        except ValueError:
            errors.append("Invalid date format for Date of Admission. Use YYYY-MM-DD.")

        try:
            if dob:
                dob = datetime.strptime(dob, '%Y-%m-%d').date()
            else:
                dob = None  # Handle empty date
        except ValueError:
            errors.append("Invalid date format for Date of Birth. Use YYYY-MM-DD.")

        # Return form with errors if validation fails
        if errors:
            return render(request, 'gym/add_customer.html', {
                'errors': errors,
                'name': name,
                'phone': phone,
                'email': email,
                'gender': gender,
                'height': height,
                'weight': weight,
                'bloodGroup': blood_group,
                'health': health,
                'date_of_admission': date_of_admission,
                'admission_number': admission_number,
                'dob': dob,
                'blood_group_choices': Customer.BLOOD_GROUP_CHOICES,  # Pass the choices to template
            })

        # If valid, save the new customer
        new_customer = Customer(
            name=name,
            phone_no=phone,
            email=email,
            gender=gender,
            height=height,
            weight=weight,
            blood_group=blood_group,
            date_of_admission=date_of_admission,
            date_of_birth=dob,
            admission_number=admission_number,
            health=health,
        )
        new_customer.save()

        return redirect('profile', customer_id=new_customer.pk)

    # Pass blood group choices to template on GET request
    return render(request, 'gym/add_customer.html', {
        'blood_group_choices': Customer.BLOOD_GROUP_CHOICES,
    })


def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect('dashboard')
    else:
        form = AuthenticationForm()
    return render(request, 'gym/login.html', {'form': form})


@login_required
def fee_details(request):
    gender = request.GET.get('gender', 'select')
    year = request.GET.get('year', timezone.now().year)
    search_query = request.GET.get('search', '').strip()

    # Filter customers by gender
    customers = Customer.objects.all()
    if gender != 'select':
        customers = customers.filter(gender=gender)

    # Filter customers by search query for name, membership ID, or phone number
    if search_query:
        customers = customers.filter(
            Q(name__icontains=search_query) |
            Q(admission_number__icontains=search_query) |
            Q(phone_no__icontains=search_query)
        )

    # Validate year
    try:
        year = int(year)
    except ValueError:
        year = timezone.now().year

    # Get current month and calculate 5 months range (previous, current, and next months)
    current_date = datetime.now()
    current_month = current_date.month
    current_year = current_date.year

    # Generate months and years for the range
    months_and_years = []
    for i in range(-1, 3):  # Previous month, current month, and next two months
        month_offset = current_month + i
        if month_offset <= 0:
            month = 12 + month_offset  # Wrap to the previous year
            year_to_add = current_year - 1
        elif month_offset > 12:
            month = month_offset - 12  # Wrap to the next year
            year_to_add = current_year + 1
        else:
            month = month_offset
            year_to_add = current_year
        months_and_years.append((month, year_to_add))

    # Map month numbers to abbreviations
    month_abbreviations = {
        1: 'Jan', 2: 'Feb', 3: 'Mar', 4: 'Apr',
        5: 'May', 6: 'Jun', 7: 'Jul', 8: 'Aug',
        9: 'Sep', 10: 'Oct', 11: 'Nov', 12: 'Dec'
    }
    months = [month_abbreviations[month] for month, _ in months_and_years]

    # Pre-fetch all relevant FeeDetails and Fee Categories in a single query
    fee_categories = CategoryTable.objects.filter(is_fees=True).values_list('id', flat=True)
    fee_details = FeeDetail.objects.filter(
        Q(month__in=[m[0] for m in months_and_years], year__in=[y[1] for y in months_and_years]),
        category_id__in=fee_categories
    ).select_related('customer')

    # Create a mapping of customer fee details
    fee_details_mapping = {}
    for fee_detail in fee_details:
        key = (fee_detail.customer_id, fee_detail.month, fee_detail.year)
        fee_details_mapping[key] = 'Paid'

    # Prepare customer fee status
    active_customers = []
    for customer in customers:
        fees_status = {}
        paid_count = 0

        for month, month_year in months_and_years:
            key = (customer.pk, month, month_year)
            if fee_details_mapping.get(key) == 'Paid':
                fees_status[month_abbreviations[month]] = 'Paid'
                paid_count += 1
            else:
                fees_status[month_abbreviations[month]] = 'Not Paid'

        # Only include customers who have paid for at least one month in the last 5 months or match search query
        if paid_count > 0 or search_query:
            active_customers.append({
                'customer': {
                    'id': customer.pk,
                    'admission_number': customer.admission_number,
                    'name': customer.name,
                },
                'fees_status': fees_status,
                'paid_count': paid_count
            })

    # Sort customers by activity (paid_count in descending order)
    active_customers.sort(key=lambda x: x['paid_count'], reverse=True)

    # Prepare the context
    context = {
        'customers': active_customers,
        'months': months,
        'year': year,
        'current_month': month_abbreviations[current_month],
    }

    # Return JSON response for AJAX requests
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse(context)

    # Render the HTML template for non-AJAX requests
    return render(request, 'gym/feeDetails.html', context)


@login_required
def dedicated(request):
    gender = request.GET.get('gender', 'select')
    search_query = request.GET.get('search', '').strip()

    # Filter customers by gender
    # customers = Customer.objects.all()
    customers = None
    if gender != 'select':
        customers = customers.filter(gender=gender)

    # Filter customers by search query for name or membership ID
    print(search_query)
    if len(search_query)>0:
        customers = customers.filter(
            models.Q(name__icontains=search_query) |
            models.Q(admission_number__icontains=search_query) |
            models.Q(phone_no__icontains=search_query)  
        )



    context = {
        'customers': customers,
    }

    # Return JSON response for AJAX requests
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse(context)

    # Render the HTML template for non-AJAX requests
    return render(request, 'gym/dedicatedpage.html', context)

@login_required
def profile_view(request, customer_id):
    customer = get_object_or_404(Customer, pk=customer_id)
    latest_fee_detail = customer.feedetail_set.order_by('-date_of_payment').first()
    if customer.date_of_birth:
        age = timezone.now().year - customer.date_of_birth.year
    else:
        age = None
    context = {
        'name': customer.name,
        'admission_number': customer.admission_number,
        'id': customer.pk,
        'gender': customer.get_gender_display(),
        'age': age,
        'email': customer.email,
        'phone': customer.phone_no,
        'height': customer.height,
        'weight': customer.weight,
        'bmi': customer.bmi,
        'bloodGroup': customer.get_blood_group_display(),
        'doj': customer.date_of_admission,
        'health': customer.health,
        # 'activeMonth': latest_fee_detail.get_month_display() if latest_fee_detail else 'N/A'
    }
    return render(request, 'gym/profile.html', context)

@login_required
def edit_customer(request, customer_id):
    customer = get_object_or_404(Customer, pk=customer_id)

    if request.method == 'POST':
        # Get the updated details from the form
        name = request.POST.get('name')
        phone = request.POST.get('phone', None)  # Default to None if not provided
        email = request.POST.get('email', None)  # Default to None if not provided
        gender = request.POST.get('gender')
        height = request.POST.get('height', None)  # Default to None if not provided
        weight = request.POST.get('weight', None)  # Default to None if not provided
        blood_group = request.POST.get('bloodGroup')
        date_of_admission = request.POST.get('date_of_admission')
        dob = request.POST.get('dob')
        health = request.POST.get('health')

        # Initialize a list to store error messages
        errors = []

        # Validate height and weight
        if height and not is_valid_number(height):
            errors.append("Height must be a valid number.")
        if weight and not is_valid_number(weight):
            errors.append("Weight must be a valid number.")

        # Validate other fields
        if not name:
            errors.append("Name is required.")
        if not gender:
            errors.append("Gender is required.")
    

        # If there are any validation errors, return to the form with errors
        if errors:
            return render(request, 'gym/edit_customer.html', {
                'customer': customer,
                'errors': errors,
                'name': name,
                'phone': phone,
                'email': email,
                'gender': gender,
                'height': height,
                'weight': weight,
                'blood_group': blood_group,
                'date_of_admission': date_of_admission,
                'dob': dob,
                'health': health
            })

        # No validation errors, so proceed to update the customer
        try:
            customer.name = name
            customer.phone_no = phone
            customer.email = email
            customer.gender = gender
            customer.height = float(height) if height else None
            customer.weight = float(weight) if weight else None
            customer.blood_group = blood_group
            customer.date_of_birth = dob
            customer.date_of_admission = date_of_admission
            customer.health = health
            customer.save()

            return redirect('profile', customer_id=customer_id)

        except Exception as e:
            # Catch any unexpected error (e.g., database issues)
            return render(request, 'gym/edit_customer.html', {'customer': customer, 'errors': [str(e)]})

    # If GET request, simply render the form
    return render(request, 'gym/edit_customer.html', {'customer': customer})


# Helper function to check if a string is a valid number
def is_valid_number(value):
    try:
        float(value)
        return True
    except ValueError:
        return False

@login_required
def pay_fees(request, customer_id):
    customer = get_object_or_404(Customer, pk=customer_id)
    categories = CategoryTable.objects.values('id', 'name').distinct()
    # Prepare the list of years (current year and previous few years)
    current_year = timezone.now().year
    years = list(range(current_year-1, current_year + 2))  # e.g., last 1 year and next year

    if request.method == 'POST':
        category_id = request.POST.get('category')
        amount = request.POST.get('amount')
        month = request.POST.get('month')
        year = request.POST.get('year')  # Get the year from the form
        dop = request.POST.get('dop')
        category_instance = get_object_or_404(CategoryTable, id=category_id)
        
        # Parse the form inputs to the appropriate types
        amount = float(amount)
        
        # Map month names to numbers
        month_mapping = {
            "January": 1, "February": 2, "March": 3, "April": 4, 
            "May": 5, "June": 6, "July": 7, "August": 8, 
            "September": 9, "October": 10, "November": 11, "December": 12
        }

        # Convert month name to an integer
        month = month_mapping.get(month)
        if month is None:
            raise ValueError("Invalid month selected")

        # Convert the year to an integer
        year = int(year)

        # Calculate the installment amount for each month
        installment_amount = amount / category_instance.no_of_months
        
        # Start creating FeeDetail entries for each month
        for i in range(category_instance.no_of_months):
            # Calculate the month and year for this installment
            current_month = (month + i - 1) % 12 + 1  # Wrap around the months (1-12)
            current_year_adjusted = year + (month + i - 1) // 12  # Adjust year for month overflow
            try:
            # Create a FeeDetail entry for the specific month and year
                fee_detail = FeeDetail(
                    customer=customer,
                    amount_paid=installment_amount,
                    date_of_payment=dop if dop else timezone.now(),
                    category=category_instance,
                    month=current_month,
                    year=current_year_adjusted
                )
                fee_detail.save()
            except IntegrityError:
                # Skip saving the FeeDetail if it already exists
                return JsonResponse({'error': 'Fee already paid for this month'})


        # Redirect back to the fee details page after saving
        return redirect('feeDetails')

    # If the request is GET, show the form
    context = {
        'customer': customer,
        'years': years,  # Pass the list of years to the template
        'categories': categories
    }
    
    return render(request, 'gym/pay_fees.html', context)


def customer_fee_details(request, customer_id):
    customer = get_object_or_404(Customer, pk=customer_id)
    fee_details = FeeDetail.objects.filter(customer=customer).order_by('year', 'month')
    
    context = {
        'customer': customer,
        'fee_details': fee_details,
    }
    return render(request, 'gym/customer_fee_details.html', context)



def get_fees(request, id):
    category = get_object_or_404(CategoryTable, pk=id)
    return JsonResponse({'fee': category.price})

