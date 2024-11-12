
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from .models import Customer, FeeDetail, CategoryTable
# from .forms import CustomerForm, FeePaymentForm
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import AuthenticationForm
import datetime
from datetime import datetime
from django.db import models

@login_required
def dashboard(request):
    data = {}
    data['no_of_customers'] = Customer.objects.count()
    data['no_of_male'] = Customer.objects.filter(gender='M').count()
    data['no_of_female'] = Customer.objects.filter(gender='F').count()
    fee_id = get_object_or_404(CategoryTable,name='Fees')
    # Calculate the last 3 months including potential year transitions
    current_date = datetime.now()
    current_month = current_date.month
    current_year = current_date.year

    # Generate month and year combinations for the last 3 months
    months_and_years = []
    for i in range(3):  # Adjust for 3 past months
        month_offset = current_month - i
        if month_offset <= 0:
            month = 12 + month_offset
            year_to_add = current_year - 1
        else:
            month = month_offset
            year_to_add = current_year
        months_and_years.append((month, year_to_add))

    # Filter active male and female customers who paid within the last 3 months
    active_male_count = 0
    active_female_count = 0

    for customer in Customer.objects.all():
        paid_count = 0  # Track payments for each customer

        # Check if the customer has any FeeDetail entry in the last 3 months
        for month, year in months_and_years:
            if FeeDetail.objects.filter(customer=customer, month=month, year=year,category=fee_id.pk).exists():
                paid_count += 1

        # If paid in any month of the last 3 months, count as active
        if paid_count > 0:
            if customer.gender == 'M':
                active_male_count += 1
            elif customer.gender == 'F':
                active_female_count += 1

    # Populate active counts
    data['no_of_active_males'] = active_male_count
    data['no_of_active_females'] = active_female_count

    return render(request, 'gym/dashboard.html', data)


def logout_view(request):
    logout(request)
    return redirect('login')

@login_required
def add_customer(request):
    if request.method == 'POST':
        admission_number = request.POST.get('admission_number')
        name = request.POST.get('name')
        phone = request.POST.get('phone', None)  # Default to None if not provided
        email = request.POST.get('email', None)  # Default to None if not provided
        gender = request.POST.get('gender')
        height = request.POST.get('height', None)  # Default to None if not provided
        weight = request.POST.get('weight', None)  # Default to None if not provided
        blood_group = request.POST.get('bloodGroup')
        dob = request.POST.get('dob')
        # Validate and save form data
        try:
            new_customer = Customer(
                admission_number=admission_number,
                name=name,
                phone_no=phone,
                email=email,
                gender=gender,
                height=float(height) if height else None,
                weight=float(weight) if weight else None,
                blood_group=blood_group,
                date_of_birth=dob,
                date_of_admission=timezone.now()
            )
            new_customer.save()
            return redirect('profile', customer_id=new_customer.pk)
        except ValueError:
           return render(request,'gym/add_customer.html', {'error': 'Invalid input. Please enter valid data.'})

   

    return render(request, 'gym/add_customer.html')



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

    # Filter customers by search query for name or membership ID
    if search_query:
        customers = customers.filter(
            models.Q(name__icontains=search_query) |
            models.Q(admission_number__icontains=search_query) |
            models.Q(phone_no__icontains=search_query)
        )

    # Validate year
    try:
        year = int(year)
    except ValueError:
        year = timezone.now().year

    # Get the current date and month
    current_date = datetime.now()
    current_month = current_date.month 
    current_year = current_date.year

    # Calculate last four months including possible year transitions
    months_and_years = []
    for i in range(3):  # Show 3 past months + current
        month_offset = current_month - i
        if month_offset <= 0:
            # Handle previous year case
            month = 12 + month_offset  # Negative values will wrap around to previous year
            year_to_add = current_year - 1
        else:
            month = month_offset
            year_to_add = current_year
        months_and_years.append((month, year_to_add))

    # Map month numbers to their abbreviations
    month_abbreviations = {
        1: 'Jan', 2: 'Feb', 3: 'Mar', 4: 'Apr',
        5: 'May', 6: 'Jun', 7: 'Jul', 8: 'Aug',
        9: 'Sep', 10: 'Oct', 11: 'Nov', 12: 'Dec'
    }

    months = [month_abbreviations[month] for month, _ in months_and_years]

    # Create a list to hold the customer fee details, only for those who paid in the last 4 months
    active_customers = []
    for customer in customers:
        # Initialize a dictionary to store fee status for each displayed month
        fees_status = {}
        paid_count = 0

        for month, month_year in months_and_years:
            # Fetch the FeeDetail object for the specific month and year
            fee_id = get_object_or_404(CategoryTable,name='Fees')
            fee_detail = FeeDetail.objects.filter(customer=customer, year=month_year, month=month,category=fee_id.pk).first()
            if fee_detail:
                # If fee is paid, store the category and increment paid_count
                fees_status[month_abbreviations[month]] = 'Paid'
                paid_count += 1
            else:
                # If no fee is paid, store 'Not Paid'
                fees_status[month_abbreviations[month]] = 'Not Paid'

        # Only include customers who have paid for at least one month in the last 4 months
        if paid_count > 0 or search_query:
            active_customers.append({
                'customer': {
                    'id': customer.pk,
                    'admission_number': customer.admission_number,
                    'name': customer.name,
                },
                'fees_status': fees_status,
                'paid_count': paid_count  # Track how many months they paid
            })

    # Sort customers by activity (paid_count in descending order)
    active_customers.sort(key=lambda x: x['paid_count'], reverse=True)
    
    context = {
        'customers': active_customers,
        'months': months,
        'year': year,
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
        'category': latest_fee_detail.get_category_display() if latest_fee_detail else 'N/A',
        'activeMonth': latest_fee_detail.get_month_display() if latest_fee_detail else 'N/A'
    }
    return render(request, 'gym/profile.html', context)
@login_required
def edit_customer(request, customer_id):
    customer = get_object_or_404(Customer, pk=customer_id)

    if request.method == 'POST':
        # Get the updated details from the form
        name = request.POST.get('name')
        phone = request.POST.get('phone', None)
        email = request.POST.get('email', None)
        gender = request.POST.get('gender')
        height = request.POST.get('height', None)
        weight = request.POST.get('weight', None)
        blood_group = request.POST.get('bloodGroup')
        dob = request.POST.get('dob')

        try:
            # Update the customer details
            customer.name = name
            customer.phone_no = phone
            customer.email = email
            customer.gender = gender
            customer.height = float(height) if height else None
            customer.weight = float(weight) if weight else None
            customer.blood_group = blood_group
            customer.date_of_birth = dob  # Ensure dob is in 'YYYY-MM-DD' format
            customer.save()

            return redirect('profile', customer_id=customer_id)
        except ValueError:
            return render(request, 'gym/edit_customer.html', {'error': 'Invalid input. Please enter valid data.', 'customer': customer})

    return render(request, 'gym/edit_customer.html', {'customer': customer})
@login_required
def pay_fees(request, customer_id):
    customer = get_object_or_404(Customer, pk=customer_id)
    categories = CategoryTable.objects.values('id', 'name').distinct()
    # Prepare the list of years (current year and previous few years)
    current_year = timezone.now().year
    years = list(range(current_year, current_year + 2))  # e.g., last 1 year and next year

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

        # Create FeeDetail entry
        fee_detail = FeeDetail(
            customer=customer,
            amount_paid=amount,
            date_of_payment=dop if dop else timezone.now(),
            category=category_instance,
            month=month,
            year=year  # Save the selected year
        )
        fee_detail.save()

        # Redirect back to the fee details page after saving
        return redirect('feeDetails')

    # If the request is GET, show the form
    context = {
        'customer': customer,
        'years': years,  # Pass the list of years to the template
        'categories':categories

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

