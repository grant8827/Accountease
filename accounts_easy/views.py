from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, authenticate
from django.contrib.auth.forms import UserCreationForm
from django.contrib import messages
from django.http import HttpResponseForbidden, Http404
from django.db.models import Count, Sum
from django.utils import timezone
from decimal import Decimal, InvalidOperation
from .models import (
    Business, Employee, Transaction, BusinessUser, 
    Deduction, PayrollConfiguration, PayrollReport, 
    EmployeeYTD, EmployeeBonus
)


@login_required
def edit_transaction(request, transaction_id):
    business = get_user_business(request.user)
    if not business:
        messages.error(request, "You don't have access to any approved business.")
        return render(request, 'accounts_easy/register_business.html', {})
    try:
        transaction = Transaction.objects.get(id=transaction_id, business=business)
    except Transaction.DoesNotExist:
        raise Http404("Transaction not found.")

    if request.method == 'POST':
        transaction_type = request.POST.get('transaction_type')
        amount = request.POST.get('amount')
        description = request.POST.get('description')
        date = request.POST.get('date')
        if transaction_type and amount and date:
            transaction.transaction_type = transaction_type
            transaction.amount = amount
            transaction.description = description
            transaction.date = date
            transaction.save()
            messages.success(request, "Transaction updated successfully!")
            return redirect('accounts_easy:view_transactions')
        else:
            messages.error(request, "Please fill in all required fields.")

    return render(request, 'accounts_easy/edit_transaction.html', {
        'business': business,
        'transaction': transaction
    })

# Delete Transaction
@login_required
def delete_transaction(request, transaction_id):
    business = get_user_business(request.user)
    if not business:
        messages.error(request, "You don't have access to any approved business.")
        return render(request, 'accounts_easy/register_business.html', {})
    try:
        transaction = Transaction.objects.get(id=transaction_id, business=business)
    except Transaction.DoesNotExist:
        raise Http404("Transaction not found.")

    if request.method == 'POST':
        transaction.delete()
        messages.success(request, "Transaction deleted successfully!")
        return redirect('accounts_easy:view_transactions')

    return render(request, 'accounts_easy/delete_transaction.html', {
        'business': business,
        'transaction': transaction
    })


@login_required
def add_transaction(request):
    """View to add a new income or expenditure transaction."""
    business = get_user_business(request.user)
    if not business:
        messages.error(request, "You don't have access to any approved business.")
        return render(request, 'accounts_easy/register_business.html', {})

    if request.method == 'POST':
        transaction_type = request.POST.get('transaction_type')
        amount = request.POST.get('amount')
        description = request.POST.get('description')
        date = request.POST.get('date')

        if transaction_type and amount and date:
            try:
                Transaction.objects.create(
                    business=business,
                    transaction_type=transaction_type,
                    amount=Decimal(amount),
                    description=description,
                    date=date,
                    created_by=request.user
                )
                messages.success(request, "Transaction added successfully!")
                return redirect('accounts_easy:view_transactions')
            except (ValueError, InvalidOperation):
                messages.error(request, "Please enter a valid amount.")
        else:
            messages.error(request, "Please fill in all required fields.")

    return render(request, 'accounts_easy/add_transaction.html', {
        'business': business
    })


@login_required
def view_transactions(request):
    """View to display all transactions for the business."""
    business = get_user_business(request.user)
    if not business:
        messages.error(request, "You don't have access to any approved business.")
        return render(request, 'accounts_easy/register_business.html', {})

    # Get filter parameters
    transaction_type = request.GET.get('type', '')
    month = request.GET.get('month', '')
    year = request.GET.get('year', '')

    # Build query
    transactions = Transaction.objects.filter(business=business)

    if transaction_type:
        transactions = transactions.filter(transaction_type=transaction_type)
    if month:
        transactions = transactions.filter(date__month=month)
    if year:
        transactions = transactions.filter(date__year=year)

    transactions = transactions.order_by('-date')

    return render(request, 'accounts_easy/view_transactions.html', {
        'business': business,
        'transactions': transactions
    })


def home(request):
    """Home page view."""
    if request.user.is_authenticated:
        return redirect('accounts_easy:dashboard')
    
    # Stats for homepage
    total_businesses = Business.objects.count()
    total_employees = Employee.objects.count()
    # total_payroll_runs = PayrollRun.objects.count()  # Disabled - model doesn't exist
    
    context = {
        'total_businesses': total_businesses,
        'total_employees': total_employees,
        # 'total_payroll_runs': total_payroll_runs,  # Disabled
    }
    
    return render(request, 'accounts_easy/home.html', context)


def get_user_business(user):
    """Helper function to get user's business."""
    # Get the first approved business for this user (in case there are multiple)
    business = Business.objects.filter(owner=user, status='approved').first()
    if business:
        return business
    
    # If no owned business, check if user has access through BusinessUser
    try:
        business_user = BusinessUser.objects.get(user=user, is_active=True)
        return business_user.business if business_user.business.is_approved else None
    except BusinessUser.DoesNotExist:
        return None


@login_required
def dashboard(request):
    """Dashboard view for authenticated users."""
    # Check if user is superuser
    if request.user.is_superuser:
        return redirect('accounts_easy:admin_dashboard')
    
    # Get user's business
    business = get_user_business(request.user)
    
    if not business:
        # Check if user has pending business registration
        try:
            pending_business = Business.objects.get(owner=request.user, status='pending')
            return render(request, 'accounts_easy/pending_approval.html', {
                'business': pending_business
            })
        except Business.DoesNotExist:
            # No business found, redirect to register
            messages.info(request, "Please register your business to access the system.")
            return redirect('accounts_easy:register_business')
    
    # Business exists and approved
    if business.is_approved:
        context = {
            'business': business,
            'total_employees': business.employees.filter(is_active=True).count(),
            # 'total_payroll_runs': PayrollRun.objects.filter(business=business).count(),  # Disabled
            # 'recent_payroll_runs': PayrollRun.objects.filter(business=business).order_by('-created_at')[:5],  # Disabled
            'recent_transactions': business.transactions.order_by('-created_at')[:5],
            'employee_count': business.employees.count(),
            'total_bonuses': EmployeeBonus.objects.filter(employee__business=business).count(),
        }
        return render(request, 'accounts_easy/dashboard.html', context)
    else:
        return render(request, 'accounts_easy/pending_approval.html', {
            'business': business
        })


@login_required
def admin_dashboard(request):
    """Admin dashboard view."""
    if not request.user.is_superuser:
        return HttpResponseForbidden("You don't have permission to access this page.")
    
    # Get businesses by status
    pending_businesses = Business.objects.filter(status='pending').order_by('-created_at')
    approved_businesses = Business.objects.filter(status='approved').order_by('-created_at')[:10]
    rejected_businesses = Business.objects.filter(status='rejected').order_by('-created_at')[:10]
    
    context = {
        'total_businesses': Business.objects.count(),
        'total_pending': pending_businesses.count(),
        'total_approved': Business.objects.filter(status='approved').count(),
        'total_rejected': Business.objects.filter(status='rejected').count(),
        'pending_businesses': pending_businesses,
        'approved_businesses': approved_businesses,
        'rejected_businesses': rejected_businesses,
        'total_employees': Employee.objects.count(),
        # 'total_payroll_runs': PayrollRun.objects.count(),  # Disabled
        'recent_businesses': Business.objects.order_by('-created_at')[:10],
    }
    
    return render(request, 'accounts_easy/admin_dashboard.html', context)


def register_user(request):
    """User registration view."""
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            username = form.cleaned_data.get('username')
            messages.success(request, f'Account created for {username}!')
            return redirect('accounts_easy:register_business')
    else:
        form = UserCreationForm()
    return render(request, 'registration/register.html', {'form': form})


@login_required
def register_business(request):
    """Business registration view."""
    if request.method == 'POST':
        name = request.POST.get('name')
        registration_number = request.POST.get('registration_number')
        address = request.POST.get('address')
        phone = request.POST.get('phone')
        email = request.POST.get('email')
        tax_id = request.POST.get('tax_id')
        
        if name and address and email:
            Business.objects.create(
                name=name,
                registration_number=registration_number,
                address=address,
                phone=phone,
                email=email,
                tax_id=tax_id,
                owner=request.user,
                status='pending'
            )
            messages.success(request, "Business registration submitted for approval!")
            return redirect('accounts_easy:dashboard')
        else:
            messages.error(request, "Please fill in all required fields.")
    
    return render(request, 'accounts_easy/register_business.html')


@login_required
def employee_detail(request, pk):
    """Employee detail view."""
    business = get_user_business(request.user)
    if not business:
        messages.error(request, "You don't have access to any approved business.")
        return redirect('accounts_easy:dashboard')
    
    employee = get_object_or_404(Employee, pk=pk, business=business)
    # employee_deductions = EmployeeDeduction.objects.filter(employee=employee).order_by('-effective_date')  # Disabled
    # payslips = Payslip.objects.filter(employee=employee).order_by('-payroll_run__end_date')  # Disabled
    
    context = {
        'business': business,
        'employee': employee,
        # 'employee_deductions': employee_deductions,  # Disabled
        # 'payslips': payslips,  # Disabled
    }
    
    return render(request, 'accounts_easy/employee_detail.html', context)


@login_required
def employee_list(request):
    """Employee list view."""
    business = get_user_business(request.user)
    if not business:
        messages.error(request, "You don't have access to any approved business.")
        return redirect('accounts_easy:dashboard')
    
    employees = business.employees.filter(is_active=True).order_by('last_name', 'first_name')
    # deduction_types = DeductionType.objects.filter(business=business).order_by('name')  # Disabled
    
    context = {
        'business': business,
        'employees': employees,
        # 'deduction_types': deduction_types,  # Disabled
    }
    
    return render(request, 'accounts_easy/employee_list.html', context)


@login_required
def payroll_list(request):
    """Payroll runs list view."""
    business = get_user_business(request.user)
    if not business:
        messages.error(request, "You don't have access to any approved business.")
        return redirect('accounts_easy:dashboard')
    
    # payroll_runs = PayrollRun.objects.filter(business=business).order_by('-end_date')  # Disabled
    
    context = {
        'business': business,
        # 'payroll_runs': payroll_runs,  # Disabled
    }
    
    return render(request, 'accounts_easy/payroll_list.html', context)


# Minimal implementations for essential views
@login_required
def bonus_management(request):
    """Bonus management view."""
    business = get_user_business(request.user)
    if not business:
        messages.error(request, "You don't have access to any approved business.")
        return redirect('accounts_easy:dashboard')
    
    bonuses = EmployeeBonus.objects.filter(employee__business=business).order_by('-created_at')
    
    context = {
        'business': business,
        'bonuses': bonuses,
    }
    
    return render(request, 'accounts_easy/bonus_management.html', context)


# Essential views with proper implementation
@login_required
def add_employee(request):
    """Add new employee view."""
    business = get_user_business(request.user)
    if not business:
        messages.error(request, "You don't have access to any approved business.")
        return redirect('accounts_easy:dashboard')
    
    if request.method == 'POST':
        employee_id = request.POST.get('employee_id')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        email = request.POST.get('email')
        phone = request.POST.get('phone')
        job_title = request.POST.get('job_title')
        basic_salary = request.POST.get('basic_salary')
        date_of_hire = request.POST.get('date_of_hire')
        
        if employee_id and first_name and last_name and email and job_title and basic_salary and date_of_hire:
            try:
                Employee.objects.create(
                    business=business,
                    employee_id=employee_id,
                    first_name=first_name,
                    last_name=last_name,
                    email=email,
                    phone=phone,
                    job_title=job_title,
                    basic_salary=Decimal(basic_salary),
                    date_of_hire=date_of_hire
                )
                messages.success(request, f"Employee {first_name} {last_name} added successfully!")
                return redirect('accounts_easy:employee_management')
            except Exception as e:
                messages.error(request, f"Error adding employee: {str(e)}")
        else:
            messages.error(request, "Please fill in all required fields.")
    
    context = {
        'business': business,
    }
    return render(request, 'accounts_easy/add_employee.html', context)

@login_required
def employee_management(request):
    """Employee management view."""
    business = get_user_business(request.user)
    if not business:
        messages.error(request, "You don't have access to any approved business.")
        return redirect('accounts_easy:dashboard')
    
    employees = business.employees.filter(is_active=True).order_by('last_name', 'first_name')
    
    context = {
        'business': business,
        'employees': employees,
    }
    return render(request, 'accounts_easy/employee_management.html', context)

@login_required
def edit_employee(request, employee_id):
    """Edit employee view."""
    business = get_user_business(request.user)
    if not business:
        messages.error(request, "You don't have access to any approved business.")
        return redirect('accounts_easy:dashboard')
    
    try:
        employee = Employee.objects.get(id=employee_id, business=business)
    except Employee.DoesNotExist:
        messages.error(request, "Employee not found.")
        return redirect('accounts_easy:employee_management')
    
    if request.method == 'POST':
        employee.first_name = request.POST.get('first_name', employee.first_name)
        employee.last_name = request.POST.get('last_name', employee.last_name)
        employee.email = request.POST.get('email', employee.email)
        employee.phone = request.POST.get('phone', employee.phone)
        employee.job_title = request.POST.get('job_title', employee.job_title)
        basic_salary = request.POST.get('basic_salary')
        if basic_salary:
            employee.basic_salary = Decimal(basic_salary)
        date_of_hire = request.POST.get('date_of_hire')
        if date_of_hire:
            employee.date_of_hire = date_of_hire
        
        employee.save()
        messages.success(request, f"Employee {employee.first_name} {employee.last_name} updated successfully!")
        return redirect('accounts_easy:employee_management')
    
    context = {
        'business': business,
        'employee': employee,
    }
    return render(request, 'accounts_easy/edit_employee.html', context)

@login_required
def business_info(request):
    """Business information view."""
    business = get_user_business(request.user)
    if not business:
        messages.error(request, "You don't have access to any approved business.")
        return redirect('accounts_easy:dashboard')
    
    context = {
        'business': business,
    }
    return render(request, 'accounts_easy/business_info.html', context)

@login_required
def business_settings(request):
    """Business settings view."""
    business = get_user_business(request.user)
    if not business:
        messages.error(request, "You don't have access to any approved business.")
        return redirect('accounts_easy:dashboard')
    
    if request.method == 'POST':
        business.name = request.POST.get('name', business.name)
        business.address = request.POST.get('address', business.address)
        business.phone = request.POST.get('phone', business.phone)
        business.email = request.POST.get('email', business.email)
        business.tax_id = request.POST.get('tax_id', business.tax_id)
        business.registration_number = request.POST.get('registration_number', business.registration_number)
        
        business.save()
        messages.success(request, "Business information updated successfully!")
        return redirect('accounts_easy:business_settings')
    
    context = {
        'business': business,
    }
    return render(request, 'accounts_easy/business_settings.html', context)

@login_required
def employee_payslips(request, employee_id):
    """Employee payslips view."""
    business = get_user_business(request.user)
    if not business:
        messages.error(request, "You don't have access to any approved business.")
        return redirect('accounts_easy:dashboard')
    
    try:
        employee = Employee.objects.get(id=employee_id, business=business)
    except Employee.DoesNotExist:
        messages.error(request, "Employee not found.")
        return redirect('accounts_easy:employee_management')
    
    # For now, show basic employee info since payslips model doesn't exist
    context = {
        'business': business,
        'employee': employee,
        'payslips': [],  # Empty until payslips model is implemented
    }
    return render(request, 'accounts_easy/employee_payslips.html', context)

@login_required
def employee_bonuses(request, employee_id):
    """Employee bonuses view."""
    business = get_user_business(request.user)
    if not business:
        messages.error(request, "You don't have access to any approved business.")
        return redirect('accounts_easy:dashboard')
    
    try:
        employee = Employee.objects.get(id=employee_id, business=business)
    except Employee.DoesNotExist:
        messages.error(request, "Employee not found.")
        return redirect('accounts_easy:employee_management')
    
    bonuses = EmployeeBonus.objects.filter(employee=employee).order_by('-created_at')
    
    context = {
        'business': business,
        'employee': employee,
        'bonuses': bonuses,
    }
    return render(request, 'accounts_easy/employee_bonuses.html', context)

@login_required
def delete_bonus(request, bonus_id):
    """Delete bonus view."""
    business = get_user_business(request.user)
    if not business:
        messages.error(request, "You don't have access to any approved business.")
        return redirect('accounts_easy:dashboard')
    
    try:
        bonus = EmployeeBonus.objects.get(id=bonus_id, employee__business=business)
    except EmployeeBonus.DoesNotExist:
        messages.error(request, "Bonus not found.")
        return redirect('accounts_easy:bonus_management')
    
    if request.method == 'POST':
        employee_name = bonus.employee.full_name
        bonus.delete()
        messages.success(request, f"Bonus for {employee_name} deleted successfully!")
        return redirect('accounts_easy:bonus_management')
    
    context = {
        'business': business,
        'bonus': bonus,
    }
    return render(request, 'accounts_easy/delete_bonus.html', context)

@login_required
def payroll_setup(request):
    """Payroll setup view."""
    business = get_user_business(request.user)
    if not business:
        messages.error(request, "You don't have access to any approved business.")
        return redirect('accounts_easy:dashboard')
    
    # Get or create payroll configuration
    try:
        payroll_config = PayrollConfiguration.objects.get(business=business)
    except PayrollConfiguration.DoesNotExist:
        payroll_config = None
    
    if request.method == 'POST':
        pay_frequency = request.POST.get('pay_frequency', 'monthly')
        tax_rate = request.POST.get('tax_rate', '0.30')
        overtime_rate = request.POST.get('overtime_rate', '1.50')
        
        if payroll_config:
            payroll_config.pay_frequency = pay_frequency
            payroll_config.tax_rate = Decimal(tax_rate)
            payroll_config.overtime_rate = Decimal(overtime_rate)
            payroll_config.save()
        else:
            PayrollConfiguration.objects.create(
                business=business,
                pay_frequency=pay_frequency,
                tax_rate=Decimal(tax_rate),
                overtime_rate=Decimal(overtime_rate)
            )
        
        messages.success(request, "Payroll configuration updated successfully!")
        return redirect('accounts_easy:payroll_setup')
    
    context = {
        'business': business,
        'payroll_config': payroll_config,
    }
    return render(request, 'accounts_easy/payroll_setup.html', context)

@login_required
def tax_setup(request):
    """Tax setup view."""
    business = get_user_business(request.user)
    if not business:
        messages.error(request, "You don't have access to any approved business.")
        return redirect('accounts_easy:dashboard')
    
    context = {
        'business': business,
    }
    return render(request, 'accounts_easy/tax_setup.html', context)

@login_required
def deduction_setup(request):
    """Deduction setup view."""
    business = get_user_business(request.user)
    if not business:
        messages.error(request, "You don't have access to any approved business.")
        return redirect('accounts_easy:dashboard')
    
    deductions = Deduction.objects.filter(business=business, is_active=True).order_by('name')
    
    if request.method == 'POST':
        name = request.POST.get('name')
        description = request.POST.get('description', '')
        deduction_type = request.POST.get('deduction_type')
        amount = request.POST.get('amount')
        is_mandatory = request.POST.get('is_mandatory') == 'on'
        is_taxable = request.POST.get('is_taxable') == 'on'
        
        if name and deduction_type and amount:
            try:
                Deduction.objects.create(
                    business=business,
                    name=name,
                    description=description,
                    deduction_type=deduction_type,
                    amount=Decimal(amount),
                    is_mandatory=is_mandatory,
                    is_taxable=is_taxable
                )
                messages.success(request, f"Deduction '{name}' created successfully!")
                return redirect('accounts_easy:deduction_setup')
            except Exception as e:
                messages.error(request, f"Error creating deduction: {str(e)}")
        else:
            messages.error(request, "Please fill in all required fields.")
    
    context = {
        'business': business,
        'deductions': deductions,
    }
    return render(request, 'accounts_easy/deduction_setup.html', context)

@login_required
def payroll_reports(request):
    """Payroll reports view."""
    business = get_user_business(request.user)
    if not business:
        messages.error(request, "You don't have access to any approved business.")
        return redirect('accounts_easy:dashboard')
    
    reports = PayrollReport.objects.filter(business=business).order_by('-pay_period_start')
    
    context = {
        'business': business,
        'reports': reports,
    }
    return render(request, 'accounts_easy/payroll_reports.html', context)

@login_required
def payroll_staff_selection(request):
    """Payroll staff selection view."""
    business = get_user_business(request.user)
    if not business:
        messages.error(request, "You don't have access to any approved business.")
        return redirect('accounts_easy:dashboard')
    
    employees = business.employees.filter(is_active=True).order_by('last_name', 'first_name')
    
    context = {
        'business': business,
        'employees': employees,
    }
    return render(request, 'accounts_easy/payroll_staff_selection.html', context)

@login_required
def create_payroll_run(request):
    """Create payroll run view."""
    business = get_user_business(request.user)
    if not business:
        messages.error(request, "You don't have access to any approved business.")
        return redirect('accounts_easy:dashboard')
    
    # Basic payroll run creation (simplified for now)
    if request.method == 'POST':
        report_name = request.POST.get('report_name')
        pay_period_start = request.POST.get('pay_period_start')
        pay_period_end = request.POST.get('pay_period_end')
        
        if report_name and pay_period_start and pay_period_end:
            try:
                PayrollReport.objects.create(
                    business=business,
                    report_name=report_name,
                    pay_period_start=pay_period_start,
                    pay_period_end=pay_period_end,
                    created_by=request.user
                )
                messages.success(request, f"Payroll run '{report_name}' created successfully!")
                return redirect('accounts_easy:payroll_reports')
            except Exception as e:
                messages.error(request, f"Error creating payroll run: {str(e)}")
        else:
            messages.error(request, "Please fill in all required fields.")
    
    context = {
        'business': business,
    }
    return render(request, 'accounts_easy/create_payroll_run.html', context)

@login_required
def payroll_run_detail(request, payroll_run_id):
    """Payroll run detail view."""
    business = get_user_business(request.user)
    if not business:
        messages.error(request, "You don't have access to any approved business.")
        return redirect('accounts_easy:dashboard')
    
    try:
        payroll_report = PayrollReport.objects.get(id=payroll_run_id, business=business)
    except PayrollReport.DoesNotExist:
        messages.error(request, "Payroll run not found.")
        return redirect('accounts_easy:payroll_reports')
    
    context = {
        'business': business,
        'payroll_report': payroll_report,
    }
    return render(request, 'accounts_easy/payroll_run_detail.html', context)

@login_required
def payslip_detail(request, payslip_id):
    """Payslip detail view (placeholder)."""
    business = get_user_business(request.user)
    if not business:
        messages.error(request, "You don't have access to any approved business.")
        return redirect('accounts_easy:dashboard')
    
    messages.info(request, "Payslip management is being developed. Please check back soon.")
    return redirect('accounts_easy:dashboard')

@login_required
def print_payslip(request, payslip_id):
    """Print payslip view (placeholder)."""
    business = get_user_business(request.user)
    if not business:
        messages.error(request, "You don't have access to any approved business.")
        return redirect('accounts_easy:dashboard')
    
    messages.info(request, "Payslip printing is being developed. Please check back soon.")
    return redirect('accounts_easy:dashboard')

@login_required
def employee_ytd(request, employee_id=None):
    """Employee YTD view."""
    business = get_user_business(request.user)
    if not business:
        messages.error(request, "You don't have access to any approved business.")
        return redirect('accounts_easy:dashboard')
    
    if employee_id:
        try:
            employee = Employee.objects.get(id=employee_id, business=business)
            ytd_records = EmployeeYTD.objects.filter(employee=employee).order_by('-year')
        except Employee.DoesNotExist:
            messages.error(request, "Employee not found.")
            return redirect('accounts_easy:employee_ytd')
    else:
        employee = None
        ytd_records = EmployeeYTD.objects.filter(employee__business=business).order_by('-year', 'employee__last_name')
    
    employees = business.employees.filter(is_active=True).order_by('last_name', 'first_name')
    
    context = {
        'business': business,
        'employee': employee,
        'ytd_records': ytd_records,
        'employees': employees,
    }
    return render(request, 'accounts_easy/employee_ytd.html', context)

@login_required
def deduction_list(request):
    """Deduction list view."""
    business = get_user_business(request.user)
    if not business:
        messages.error(request, "You don't have access to any approved business.")
        return redirect('accounts_easy:dashboard')
    
    deductions = Deduction.objects.filter(business=business).order_by('name')
    
    context = {
        'business': business,
        'deductions': deductions,
    }
    return render(request, 'accounts_easy/deduction_list.html', context)

@login_required
def payroll_run_list(request):
    """Payroll run list view."""
    business = get_user_business(request.user)
    if not business:
        messages.error(request, "You don't have access to any approved business.")
        return redirect('accounts_easy:dashboard')
    
    payroll_reports = PayrollReport.objects.filter(business=business).order_by('-pay_period_start')
    
    context = {
        'business': business,
        'payroll_reports': payroll_reports,
    }
    return render(request, 'accounts_easy/payroll_list.html', context)

@login_required
def business_directory(request):
    """Business directory view."""
    if not request.user.is_superuser:
        messages.error(request, "You don't have permission to access this page.")
        return redirect('accounts_easy:dashboard')
    
    businesses = Business.objects.filter(status='approved').order_by('name')
    
    context = {
        'businesses': businesses,
    }
    return render(request, 'accounts_easy/business_directory.html', context)

@login_required
def approve_business(request, business_id):
    if not request.user.is_superuser:
        return HttpResponseForbidden("You don't have permission to access this page.")
    
    business = get_object_or_404(Business, id=business_id)
    business.status = 'approved'
    business.save()
    messages.success(request, f"Business '{business.name}' has been approved.")
    return redirect('accounts_easy:admin_dashboard')

@login_required
def reject_business(request, business_id):
    if not request.user.is_superuser:
        return HttpResponseForbidden("You don't have permission to access this page.")
    
    business = get_object_or_404(Business, id=business_id)
    business.status = 'rejected'
    business.save()
    messages.success(request, f"Business '{business.name}' has been rejected.")
    return redirect('accounts_easy:admin_dashboard')

@login_required
def delete_business(request, business_id):
    if not request.user.is_superuser:
        return HttpResponseForbidden("You don't have permission to access this page.")
    
    business = get_object_or_404(Business, id=business_id)
    business_name = business.name
    business.delete()
    messages.success(request, f"Business '{business_name}' has been deleted.")
    return redirect('accounts_easy:admin_dashboard')
