from django.contrib.auth.decorators import login_required
from decimal import Decimal, InvalidOperation
from django.http import Http404

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
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, authenticate
from django.contrib.auth.forms import UserCreationForm
from django.contrib import messages
from django.http import HttpResponseForbidden
from django.db.models import Count, Sum
from django.utils import timezone
from .models import (
    Business, Employee, Transaction, BusinessUser, 
    Deduction, PayrollConfiguration, PayrollReport, 
    EmployeeYTD, EmployeeBonus
)



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
                    amount=amount,
                    description=description,
                    date=date
                )
                messages.success(request, "Transaction added successfully!")
                return redirect('accounts_easy:view_transactions')
            except Exception as e:
                messages.error(request, f"Error adding transaction: {str(e)}")
        else:
            messages.error(request, "Please fill in all required fields.")

    return render(request, 'accounts_easy/add_transaction.html', {'business': business})


@login_required
def view_transactions(request):
    """View to list all transactions for the business."""
    business = get_user_business(request.user)
    if not business:
        messages.error(request, "You don't have access to any approved business.")
        return render(request, 'accounts_easy/register_business.html', {})

    transactions = Transaction.objects.filter(business=business).order_by('-date')
    return render(request, 'accounts_easy/view_transactions.html', {
        'business': business,
        'transactions': transactions
    })


def home(request):
    """
    Landing page for the application.
    """
    # Get some statistics for the landing page
    total_businesses = Business.objects.count()
    total_employees = Employee.objects.count()
    total_payroll_runs = PayrollRun.objects.count()
    
    # Don't redirect to dashboard if user is authenticated to avoid potential loops
    # Instead, show the homepage with appropriate content for all users
    
    context = {
        'total_businesses': total_businesses,
        'total_employees': total_employees,
        'total_payroll_runs': total_payroll_runs,
        'user_authenticated': request.user.is_authenticated
    }
    return render(request, 'accounts_easy/home.html', context)


def get_user_business(user):
    """
    Get the approved business associated with the current user.
    Returns the first approved business the user has access to.
    """
    if not user.is_authenticated:
        return None
    
    # First check if user has a business through BusinessUser relationship
    business_user = BusinessUser.objects.filter(
        user=user,
        is_active=True
    ).select_related('business').first()
    # Check if business_user exists and business is approved (use correct field)
    if business_user and getattr(business_user.business, 'status', None) == 'approved':
        return business_user.business

    # If user is a business owner, check for approved business (use correct field)
    business = Business.objects.filter(
        owner=user,
        status='approved'
    ).first()
    return business


def get_user_pending_business(user):
    """
    Get pending business registration for the user.
    """
    if not user.is_authenticated:
        return None
    
    # If you want to get pending businesses, use status='pending'
    return Business.objects.filter(
        owner=user,
        status='pending'
    ).first()


def is_admin_user(user):
    """
    Check if user is an admin (superuser or staff).
    """
    return user.is_authenticated and (user.is_superuser or user.is_staff)


def check_business_access(user, business):
    """
    Check if user has access to the specified approved business.
    """
    if not user.is_authenticated:
        return False
    
    # Only allow access to approved businesses
    if not business.can_operate:
        return False
    
    if business.owner == user:
        return True
    
    return BusinessUser.objects.filter(
        user=user, 
        business=business, 
        is_active=True
    ).exists()


@login_required
def dashboard(request):
    try:
        business = get_user_business(request.user)
        if not business:
            messages.error(request, "You don't have access to any approved business.")
            return render(request, 'accounts_easy/register_business.html', {})
        
        context = {
            'business': business,
            'total_employees': Employee.objects.filter(business=business).count(),
            'total_payroll_runs': PayrollRun.objects.filter(business=business).count(),
            'recent_payroll_runs': PayrollRun.objects.filter(business=business).order_by('-created_at')[:5],
            'recent_employees': Employee.objects.filter(business=business).order_by('-created_at')[:5],
            'view_urls': [
                'accounts_easy:add_transaction',
                'accounts_easy:view_transactions',
            ]
        }
        return render(request, 'accounts_easy/dashboard.html', context)
    except Exception as e:
        messages.error(request, f"An error occurred: {str(e)}")
        # Instead of redirecting back to home, render a simple template to break the redirect loop
        return render(request, 'accounts_easy/home.html', {
            'total_businesses': Business.objects.count(),
            'total_employees': Employee.objects.count(),
            'total_payroll_runs': PayrollRun.objects.count(),
        })

@login_required
def employee_management(request):
    business = get_user_business(request.user)
    if not business:
        messages.error(request, "You don't have access to any approved business.")
        return render(request, 'accounts_easy/register_business.html', {})
    
    employees = Employee.objects.filter(business=business).order_by('last_name')
    return render(request, 'accounts_easy/employee_management.html', {
        'business': business,
        'employees': employees
    })

@login_required
def create_payroll_run(request):
    business = get_user_business(request.user)
    if not business:
        messages.error(request, "You don't have access to any approved business.")
        return redirect('accounts_easy:dashboard')

    if request.method == 'POST':
        try:
            # Process form submission and create payroll run
            # Your existing payroll creation logic
            pass
        except Exception as e:
            messages.error(request, f"Error creating payroll run: {str(e)}")
            return redirect('accounts_easy:payroll_staff_selection')
    
    employees = Employee.objects.filter(business=business, is_active=True)
    context = {
        'business': business,
        'employees': employees,
        'today': timezone.now().date()
    }
    return render(request, 'accounts_easy/payroll_staff_selection.html', context)
@login_required
def employee_list(request):
    """
    Displays a list of all employees for the user's business.
    """
    business = get_user_business(request.user)
    if not business:
        messages.error(request, "You don't have access to any business.")
        return render(request, 'accounts_easy/register_business.html', {})
    
    employees = Employee.objects.filter(business=business).order_by('last_name', 'first_name')
    context = {
        'employees': employees,
        'business': business,
    }
    return render(request, 'accounts_easy/employee_list.html', context)


@login_required
def employee_detail(request, pk):
    """
    Displays details for a single employee.
    """
    business = get_user_business(request.user)
    if not business:
        messages.error(request, "You don't have access to any business.")
        return redirect('accounts_easy:dashboard')
    
    employee = get_object_or_404(Employee, pk=pk, business=business)
    employee_deductions = EmployeeDeduction.objects.filter(employee=employee).order_by('-effective_date')
    payslips = Payslip.objects.filter(employee=employee).order_by('-payroll_run__end_date')

    context = {
        'employee': employee,
        'employee_deductions': employee_deductions,
        'payslips': payslips,
        'business': business,
    }
    return render(request, 'accounts_easy/employee_detail.html', context)


@login_required
def deduction_list(request):
    """
    Displays a list of all deduction types for the user's business.
    """
    business = get_user_business(request.user)
    if not business:
        messages.error(request, "You don't have access to any business.")
        return render(request, 'accounts_easy/register_business.html', {})
    
    deduction_types = DeductionType.objects.filter(business=business).order_by('name')
    context = {
        'deduction_types': deduction_types,
        'business': business,
    }
    return render(request, 'accounts_easy/deduction_list.html', context)


@login_required
def payroll_run_list(request):
    """
    Displays a list of all payroll runs for the user's business.
    """
    business = get_user_business(request.user)
    if not business:
        messages.error(request, "You don't have access to any business.")
        return render(request, 'accounts_easy/register_business.html', {})
    
    payroll_runs = PayrollRun.objects.filter(business=business).order_by('-end_date')
    context = {
        'payroll_runs': payroll_runs,
        'business': business,
    }
    return render(request, 'accounts_easy/payroll_list.html', context)


def register_business(request):
    """
    Register a new business.
    """
    if request.method == 'POST':
        # Handle business registration
        name = request.POST.get('name')
        registration_number = request.POST.get('registration_number')
        address = request.POST.get('address')
        phone = request.POST.get('phone')
        email = request.POST.get('email')
        tax_id = request.POST.get('tax_id')
        
        if name and address and email:
            business = Business.objects.create(
                name=name,
                registration_number=registration_number,
                address=address,
                phone=phone,
                email=email,
                tax_id=tax_id,
                owner=request.user
            )
            messages.success(request, f"Business '{business.name}' registered successfully!")
            return redirect('accounts_easy:dashboard')
        else:
            messages.error(request, "Please fill in all required fields.")
    
    return render(request, 'accounts_easy/register_business.html')


def register_user(request):
    """
    User registration view.
    """
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            username = form.cleaned_data.get('username')
            messages.success(request, f'Account created for {username}! You can now register your business.')
            login(request, user)
            return redirect('accounts_easy:register_business')
    else:
        form = UserCreationForm()
    
    return render(request, 'registration/register.html', {'form': form})


@login_required
def payroll_staff_selection(request):
    """
    Payroll interface with staff selection and individual salary/bonus editing.
    """
    business = get_user_business(request.user)
    if not business:
        messages.error(request, "You don't have access to any approved business.")
        return redirect('accounts_easy:dashboard')
    
    if request.method == 'POST' and 'create_payroll' in request.POST:
        # Process payroll creation for selected employees
        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date')
        run_date = request.POST.get('run_date')
        notes = request.POST.get('notes', '')
        selected_employees = request.POST.getlist('selected_employees')
        
        if not selected_employees:
            messages.error(request, "Please select at least one employee for the payroll run.")
            return redirect('accounts_easy:payroll_staff_selection')
        
        try:
            # Check if payroll run already exists for this period
            existing_payroll = PayrollRun.objects.filter(
                business=business,
                start_date=start_date,
                end_date=end_date
            ).first()
            
            if existing_payroll:
                messages.error(request, f"A payroll run already exists for the period {start_date} to {end_date}. Please choose a different date range or edit the existing payroll run.")
                return redirect('accounts_easy:payroll_staff_selection')
            
            # Create payroll run
            payroll_run = PayrollRun.objects.create(
                business=business,
                start_date=start_date,
                end_date=end_date,
                run_date=run_date,
                notes=notes,
                created_by=request.user
            )
            payslips_created = 0
            for employee_id in selected_employees:
                employee = Employee.objects.get(id=employee_id, business=business)
                basic_pay = employee.basic_salary
                
                # Calculate bonuses for this employee for the payroll period
                try:
                    payroll_month = timezone.datetime.strptime(end_date, '%Y-%m-%d').month
                    payroll_year = timezone.datetime.strptime(end_date, '%Y-%m-%d').year
                except (ValueError, TypeError):
                    payroll_month = timezone.now().month
                    payroll_year = timezone.now().year
                
                # Get pending bonuses for this month/year
                pending_bonuses = EmployeeBonus.objects.filter(
                    employee=employee,
                    month=payroll_month,
                    year=payroll_year,
                    is_applied=False
                )
                
                total_bonus = sum(bonus.amount for bonus in pending_bonuses)
                total_bonus = Decimal(str(total_bonus))
                gross_pay = basic_pay + total_bonus

                # Example deduction calculations (replace with your logic)
                paye_tax = Decimal('0.00')
                nis_deduction = Decimal('0.00')
                nht_deduction = Decimal('0.00')
                heart_deduction = Decimal('0.00')
                ed_deduction = Decimal('0.00')
                other_deductions = Decimal('0.00')
                employee_deductions = EmployeeDeduction.objects.filter(employee=employee, is_active=True)
                for deduction in employee_deductions:
                    if deduction.deduction_type.is_percentage:
                        other_deductions += gross_pay * (deduction.amount / Decimal('100'))
                    else:
                        other_deductions += deduction.amount

                payslip = Payslip.objects.create(
                    employee=employee,
                    payroll_run=payroll_run,
                    basic_pay=basic_pay,
                    bonus=total_bonus,
                    paye_tax=paye_tax,
                    nis_deduction=nis_deduction,
                    nht_deduction=nht_deduction,
                    heart_deduction=heart_deduction,
                    ed_deduction=ed_deduction,
                    other_deductions=other_deductions
                )

                # Mark bonuses as applied
                for bonus in pending_bonuses:
                    bonus.is_applied = True
                    bonus.applied_date = timezone.now()
                    bonus.save()

                # Update YTD records
                try:
                    year = timezone.datetime.strptime(end_date, '%Y-%m-%d').year
                except Exception:
                    year = timezone.now().year
                ytd_record, created = EmployeeYTD.objects.get_or_create(
                    employee=employee,
                    year=year
                )
                if hasattr(ytd_record, 'update_from_payslip'):
                    ytd_record.update_from_payslip(payslip)
                payslips_created += 1

            payroll_run.status = 'completed'
            payroll_run.save()

            messages.success(request, f"Payroll run created successfully with {payslips_created} payslips generated!")
            return redirect('accounts_easy:payroll_run_detail', payroll_run_id=payroll_run.id)
        except Exception as e:
            messages.error(request, f"Error creating payroll run: {str(e)}")
    
    # Get all active employees
    employees = Employee.objects.filter(business=business, is_active=True).order_by('last_name', 'first_name')
    current_month = timezone.now().month
    current_year = timezone.now().year

    context = {
        'business': business,
        'employees': employees,
        'today': timezone.now().date(),
        'current_month': current_month,
        'current_year': current_year
    }
    return render(request, 'accounts_easy/payroll_staff_selection.html', context)

def business_directory(request):
    """
    Public directory of approved businesses (for demo purposes).
    """
    businesses = Business.objects.filter(status='approved').order_by('name')
    
    context = {
        'businesses': businesses,
    }
    return render(request, 'accounts_easy/business_directory.html', context)


# Admin Views
@login_required
def admin_dashboard(request):
    """
    Admin dashboard for managing business approvals.
    """
    if not is_admin_user(request.user):
        messages.error(request, "You don't have permission to access the admin dashboard.")
        return render(request, 'accounts_easy/home.html', {
            'total_businesses': Business.objects.count(),
            'total_employees': Employee.objects.count(),
            'total_payroll_runs': PayrollRun.objects.count(),
            'user_authenticated': request.user.is_authenticated
        })
    
    # Get pending businesses
    pending_businesses = Business.objects.filter(status='pending').order_by('-created_at')
    approved_businesses = Business.objects.filter(status='approved').order_by('-updated_at')[:10]
    rejected_businesses = Business.objects.filter(status='rejected').order_by('-updated_at')[:10]

    # Get statistics
    total_pending = Business.objects.filter(status='pending').count()
    total_approved = Business.objects.filter(status='approved').count()
    total_rejected = Business.objects.filter(status='rejected').count()
    total_employees = Employee.objects.count()
    
    context = {
        'pending_businesses': pending_businesses,
        'approved_businesses': approved_businesses,
        'rejected_businesses': rejected_businesses,
        'total_pending': total_pending,
        'total_approved': total_approved,
        'total_rejected': total_rejected,
        'total_employees': total_employees,
    }
    return render(request, 'accounts_easy/admin_dashboard.html', context)


@login_required
def approve_business(request, business_id):
    """
    Approve a business registration.
    """
    if not is_admin_user(request.user):
        messages.error(request, "You don't have permission to approve businesses.")
        return redirect('accounts_easy:dashboard')
    
    business = get_object_or_404(Business, id=business_id)
    
    if request.method == 'POST':
        business.status = 'approved'
        business.approved_by = request.user
        business.approved_at = timezone.now()
        business.save()
        
        messages.success(request, f"Business '{business.name}' has been approved successfully.")
        return redirect('accounts_easy:admin_dashboard')
    
    context = {'business': business}
    return render(request, 'accounts_easy/approve_business.html', context)


@login_required
def reject_business(request, business_id):
    """
    Reject a business registration.
    """
    if not is_admin_user(request.user):
        messages.error(request, "You don't have permission to reject businesses.")
        return redirect('accounts_easy:dashboard')
    
    business = get_object_or_404(Business, id=business_id)
    
    if request.method == 'POST':
        rejection_reason = request.POST.get('rejection_reason', '')
        business.status = 'rejected'
        business.rejection_reason = rejection_reason
        business.save()
        
        messages.success(request, f"Business '{business.name}' has been rejected.")
        return redirect('accounts_easy:admin_dashboard')
    
    context = {'business': business}
    return render(request, 'accounts_easy/reject_business.html', context)


@login_required 
def add_employee(request):
    """
    Add a new employee to the user's business.
    """
    business = get_user_business(request.user)
    if not business:
        messages.error(request, "You don't have access to any approved business.")
        return redirect('accounts_easy:dashboard')
    
    if request.method == 'POST':
        # Extract form data
        employee_id = request.POST.get('employee_id')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        email = request.POST.get('email')
        phone = request.POST.get('phone', '')
        job_title = request.POST.get('job_title')
        basic_salary = request.POST.get('basic_salary')
        date_of_hire = request.POST.get('date_of_hire')
        
        try:
            # Check if employee ID already exists for this business
            if Employee.objects.filter(business=business, employee_id=employee_id).exists():
                messages.error(request, f"Employee ID '{employee_id}' already exists in your business.")
                return render(request, 'accounts_easy/add_employee.html', {'business': business})
            
            # Create new employee
            employee = Employee.objects.create(
                business=business,
                employee_id=employee_id,
                first_name=first_name,
                last_name=last_name,
                email=email,
                phone=phone,
                job_title=job_title,
                basic_salary=basic_salary,
                date_of_hire=date_of_hire
            )
            
            messages.success(request, f"Employee '{employee.full_name}' has been added successfully.")
            return redirect('accounts_easy:employee_list')
            
        except Exception as e:
            messages.error(request, f"Error adding employee: {str(e)}")
    
    context = {'business': business}
    return render(request, 'accounts_easy/add_employee.html', context)


# Payroll Configuration Views
@login_required
def payroll_setup(request):
    """
    Setup payroll configuration for the business.
    """
    business = get_user_business(request.user)
    if not business:
        messages.error(request, "You don't have access to any approved business.")
        return redirect('accounts_easy:dashboard')
    
    # Get or create payroll configuration
    payroll_config, created = PayrollConfiguration.objects.get_or_create(business=business)
    
    if request.method == 'POST':
        # Update payroll configuration
        payroll_config.payroll_frequency = request.POST.get('payroll_frequency', 'monthly')
        payroll_config.paye_rate = request.POST.get('paye_rate', 0.25)
        payroll_config.nis_rate = request.POST.get('nis_rate', 0.03)
        payroll_config.nht_rate = request.POST.get('nht_rate', 0.02)
        payroll_config.heart_rate = request.POST.get('heart_rate', 0.003)
        payroll_config.ed_rate = request.POST.get('ed_rate', 0.0025)
        payroll_config.paye_threshold = request.POST.get('paye_threshold', 1500000)
        payroll_config.nis_ceiling = request.POST.get('nis_ceiling', 5000000)
        payroll_config.company_nis_number = request.POST.get('company_nis_number', '')
        payroll_config.company_paye_number = request.POST.get('company_paye_number', '')
        payroll_config.overtime_rate_multiplier = request.POST.get('overtime_rate_multiplier', 1.5)
        payroll_config.standard_hours_per_week = request.POST.get('standard_hours_per_week', 40)
        
        try:
            payroll_config.save()
            messages.success(request, "Payroll configuration updated successfully!")
            return redirect('accounts_easy:payroll_setup')
        except Exception as e:
            messages.error(request, f"Error updating payroll configuration: {str(e)}")
    
    context = {
        'business': business,
        'payroll_config': payroll_config,
        'created': created
    }
    return render(request, 'accounts_easy/payroll_setup.html', context)


@login_required
def tax_setup(request):
    """
    Setup tax configuration for the business.
    """
    business = get_user_business(request.user)
    if not business:
        messages.error(request, "You don't have access to any approved business.")
        return redirect('accounts_easy:dashboard')
    
    payroll_config, created = PayrollConfiguration.objects.get_or_create(business=business)
    
    if request.method == 'POST':
        # Update tax rates
        payroll_config.paye_rate = request.POST.get('paye_rate', 0.25)
        payroll_config.nis_rate = request.POST.get('nis_rate', 0.03)
        payroll_config.nht_rate = request.POST.get('nht_rate', 0.02)
        payroll_config.heart_rate = request.POST.get('heart_rate', 0.003)
        payroll_config.ed_rate = request.POST.get('ed_rate', 0.0025)
        payroll_config.paye_threshold = request.POST.get('paye_threshold', 1500000)
        payroll_config.nis_ceiling = request.POST.get('nis_ceiling', 5000000)
        
        try:
            payroll_config.save()
            messages.success(request, "Tax configuration updated successfully!")
            return redirect('accounts_easy:tax_setup')
        except Exception as e:
            messages.error(request, f"Error updating tax configuration: {str(e)}")
    
    context = {
        'business': business,
        'payroll_config': payroll_config
    }
    return render(request, 'accounts_easy/tax_setup.html', context)


@login_required
def employee_ytd(request, employee_id=None):
    """
    View YTD records for employees.
    """
    business = get_user_business(request.user)
    if not business:
        messages.error(request, "You don't have access to any approved business.")
        return redirect('accounts_easy:dashboard')
    
    current_year = timezone.now().year
    employees = Employee.objects.filter(business=business, is_active=True)
    
    if employee_id:
        employee = get_object_or_404(Employee, id=employee_id, business=business)
        ytd_record, created = EmployeeYTD.objects.get_or_create(
            employee=employee, 
            year=current_year
        )
        context = {
            'business': business,
            'employee': employee,
            'ytd_record': ytd_record,
            'current_year': current_year
        }
        return render(request, 'accounts_easy/employee_ytd_detail.html', context)
    
    # Get YTD records for all employees
    ytd_records = EmployeeYTD.objects.filter(
        employee__business=business,
        year=current_year
    ).select_related('employee')
    
    # Create YTD records for employees who don't have them
    existing_employee_ids = set(ytd_records.values_list('employee_id', flat=True))
    for employee in employees:
        if employee.id not in existing_employee_ids:
            EmployeeYTD.objects.create(employee=employee, year=current_year)
    
    # Refresh the queryset
    ytd_records = EmployeeYTD.objects.filter(
        employee__business=business,
        year=current_year
    ).select_related('employee')
    
    context = {
        'business': business,
        'ytd_records': ytd_records,
        'current_year': current_year,
        'employees': employees
    }
    return render(request, 'accounts_easy/employee_ytd.html', context)


@login_required
def deduction_setup(request):
    """
    Setup and manage deduction types for the business.
    """
    business = get_user_business(request.user)
    if not business:
        messages.error(request, "You don't have access to any approved business.")
        return redirect('accounts_easy:dashboard')
    
    if request.method == 'POST':
        # Add new deduction type
        name = request.POST.get('name')
        description = request.POST.get('description', '')
        is_percentage = request.POST.get('is_percentage') == 'on'
        default_value = request.POST.get('default_value', 0)
        
        try:
            DeductionType.objects.create(
                business=business,
                name=name,
                description=description,
                is_percentage=is_percentage,
                default_value=default_value
            )
            messages.success(request, f"Deduction type '{name}' added successfully!")
            return redirect('accounts_easy:deduction_setup')
        except Exception as e:
            messages.error(request, f"Error adding deduction type: {str(e)}")
    
    deduction_types = DeductionType.objects.filter(business=business, is_active=True)
    
    context = {
        'business': business,
        'deduction_types': deduction_types
    }
    return render(request, 'accounts_easy/deduction_setup.html', context)


@login_required
def employee_management(request):
    """
    Comprehensive employee management interface.
    """
    business = get_user_business(request.user)
    if not business:
        messages.error(request, "You don't have access to any approved business.")
        return redirect('accounts_easy:dashboard')
    
    employees = Employee.objects.filter(business=business).order_by('last_name', 'first_name')
    
    # Get employee statistics
    total_employees = employees.count()
    active_employees = employees.filter(is_active=True).count()
    recent_hires = employees.filter(
        date_of_hire__gte=timezone.now().date() - timezone.timedelta(days=30)
    ).count()
    
    context = {
        'business': business,
        'employees': employees,
        'total_employees': total_employees,
        'active_employees': active_employees,
        'recent_hires': recent_hires
    }
    return render(request, 'accounts_easy/employee_management.html', context)


@login_required
def edit_employee(request, employee_id):
    """
    Edit employee information.
    """
    business = get_user_business(request.user)
    if not business:
        messages.error(request, "You don't have access to any approved business.")
        return redirect('accounts_easy:dashboard')
    
    employee = get_object_or_404(Employee, id=employee_id, business=business)
    
    if request.method == 'POST':
        # Update employee information
        employee.first_name = request.POST.get('first_name')
        employee.last_name = request.POST.get('last_name')
        employee.email = request.POST.get('email')
        employee.phone = request.POST.get('phone', '')
        employee.job_title = request.POST.get('job_title')
        employee.basic_salary = request.POST.get('basic_salary')
        employee.date_of_hire = request.POST.get('date_of_hire')
        employee.is_active = request.POST.get('is_active') == 'on'
        
        try:
            employee.save()
            messages.success(request, f"Employee '{employee.full_name}' updated successfully!")
            return redirect('accounts_easy:employee_management')
        except Exception as e:
            messages.error(request, f"Error updating employee: {str(e)}")
    
    context = {
        'business': business,
        'employee': employee
    }
    return render(request, 'accounts_easy/edit_employee.html', context)


@login_required
def payroll_reports(request):
    """
    Generate and view payroll reports.
    """
    business = get_user_business(request.user)
    if not business:
        messages.error(request, "You don't have access to any approved business.")
        return redirect('accounts_easy:dashboard')
    
    if request.method == 'POST':
        report_type = request.POST.get('report_type')
        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date')
        
        # Generate report based on type
        if report_type == 'ytd_summary':
            current_year = timezone.now().year
            ytd_records = EmployeeYTD.objects.filter(
                employee__business=business,
                year=current_year
            ).select_related('employee')
            
            report_data = {
                'total_employees': ytd_records.count(),
                'total_gross_pay': sum(record.ytd_gross_pay for record in ytd_records),
                'total_net_pay': sum(record.ytd_net_pay for record in ytd_records),
                'total_deductions': sum(record.ytd_total_deductions for record in ytd_records),
                'employees': [
                    {
                        'name': record.employee.full_name,
                        'gross_pay': float(record.ytd_gross_pay),
                        'net_pay': float(record.ytd_net_pay),
                        'deductions': float(record.ytd_total_deductions)
                    }
                    for record in ytd_records
                ]
            }
            
            PayrollReport.objects.create(
                business=business,
                report_type=report_type,
                report_period_start=f"{current_year}-01-01",
                report_period_end=f"{current_year}-12-31",
                report_data=report_data,
                generated_by=request.user
            )
            
            messages.success(request, "YTD Summary report generated successfully!")
    
    reports = PayrollReport.objects.filter(business=business).order_by('-generated_at')[:10]
    
    context = {
        'business': business,
        'reports': reports
    }
    return render(request, 'accounts_easy/payroll_reports.html', context)


@login_required
def delete_business(request, business_id):
    """
    Delete a business (Admin only).
    """
    if not is_admin_user(request.user):
        messages.error(request, "You don't have permission to delete businesses.")
        return redirect('accounts_easy:dashboard')
    
    business = get_object_or_404(Business, id=business_id)
    
    if request.method == 'POST':
        business_name = business.name
        business.delete()
        
        messages.success(request, f"Business '{business_name}' and all its data has been permanently deleted.")
        return redirect('accounts_easy:admin_dashboard')
    
    # Get counts of related data that will be deleted
    employee_count = Employee.objects.filter(business=business).count()
    payroll_runs_count = PayrollRun.objects.filter(business=business).count()
    
    context = {
        'business': business,
        'employee_count': employee_count,
        'payroll_runs_count': payroll_runs_count,
    }
    return render(request, 'accounts_easy/delete_business.html', context)




@login_required
def create_payroll_run(request):
    business = get_user_business(request.user)
    if not business:
        messages.error(request, "You don't have access to any approved business.")
        return redirect('accounts_easy:dashboard')
    # Process payroll creation for selected employees
    start_date = request.POST.get('start_date')
    end_date = request.POST.get('end_date')
    run_date = request.POST.get('run_date')
    notes = request.POST.get('notes', '')
    selected_employees = request.POST.getlist('selected_employees')
    
    if not selected_employees:
        messages.error(request, "Please select at least one employee for the payroll run.")
        return redirect('accounts_easy:payroll_staff_selection')
    
    try:
        # Create payroll run
        payroll_run = PayrollRun.objects.create(
            business=business,
            start_date=start_date,
            end_date=end_date,
            run_date=run_date,
            notes=notes,
            created_by=request.user
        )
        
        # Create payroll records for selected employees
        for employee_id in selected_employees:
            employee = Employee.objects.get(id=employee_id, business=business)
            basic_pay = employee.basic_salary
            total_bonus = 0  # No EmployeeBonus model in context
            gross_pay = basic_pay + total_bonus

            # Calculate deductions
            paye_tax = 0
            nis_deduction = 0
            nht_deduction = 0
            heart_deduction = 0
            ed_deduction = 0
            other_deductions = 0
            employee_deductions = EmployeeDeduction.objects.filter(employee=employee, is_active=True)
            for deduction in employee_deductions:
                if deduction.deduction_type.is_percentage:
                    other_deductions += gross_pay * (deduction.amount / 100)
                else:
                    other_deductions += deduction.amount
            
            # Calculate net pay
            total_deductions = paye_tax + nis_deduction + nht_deduction + heart_deduction + ed_deduction + other_deductions
            # Create payslip
            payslip = Payslip.objects.create(
                employee=employee,
                payroll_run=payroll_run,
                basic_pay=basic_pay,
                bonus=total_bonus,
                paye_tax=paye_tax,
                nis_deduction=nis_deduction,
                nht_deduction=nht_deduction,
                heart_deduction=heart_deduction,
                ed_deduction=ed_deduction,
                other_deductions=other_deductions
            )
            
            # No EmployeeBonus to mark as applied
            
            # Update YTD records
            ytd_record, created = EmployeeYTD.objects.get_or_create(
                employee=employee,
                year=timezone.datetime.strptime(end_date, '%Y-%m-%d').year
            )
            ytd_record.update_from_payslip(payslip)
            
            payslips_created += 1
        
        payroll_run.status = 'completed'
        payroll_run.save()
        
        messages.success(request, f"Payroll run created successfully with {payslips_created} payslips generated!")
        return redirect('accounts_easy:payroll_run_detail', payroll_run_id=payroll_run.id)
        
    except Exception as e:
        messages.error(request, f"Error creating payroll run: {str(e)}")
    # Get all active employees
    employees = Employee.objects.filter(business=business, is_active=True).order_by('last_name', 'first_name')
    current_month = timezone.now().month
    current_year = timezone.now().year
    # No EmployeeBonus, so no current_bonuses field needed
    
    context = {
        'business': business,
        'employees': employees,
        'today': timezone.now().date(),
        'current_month': current_month,
        'current_year': current_year
    }
    return render(request, 'accounts_easy/payroll_staff_selection.html', context)


@login_required
def create_payroll_run(request):
    """
    Create a new payroll run and generate payslips.
    """
    business = get_user_business(request.user)
    if not business:
        messages.error(request, "You don't have access to any approved business.")
        return redirect('accounts_easy:dashboard')
    
    if request.method == 'POST':
        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date')
        run_date = request.POST.get('run_date')
        notes = request.POST.get('notes', '')
        
        try:
            # Get payroll configuration first
            try:
                payroll_config = PayrollConfiguration.objects.get(business=business)
            except PayrollConfiguration.DoesNotExist:
                messages.error(request, "Payroll configuration not found. Please set up payroll configuration before creating a payroll run.")
                return redirect('accounts_easy:payroll_setup')
            
            # Check if payroll run already exists for this period
            existing_payroll = PayrollRun.objects.filter(
                business=business,
                start_date=start_date,
                end_date=end_date
            ).first()
            
            if existing_payroll:
                messages.error(request, f"A payroll run already exists for the period {start_date} to {end_date}. Please choose a different date range or edit the existing payroll run.")
                return redirect('accounts_easy:create_payroll_run')
            
            # Create payroll run
            payroll_run = PayrollRun.objects.create(
                business=business,
                start_date=start_date,
                end_date=end_date,
                run_date=run_date,
                notes=notes,
                created_by=request.user
            )
            
            # Generate payslips for all active employees
            employees = Employee.objects.filter(business=business, is_active=True)
            payslips_created = 0
            errors = []
            
            if not employees.exists():
                messages.warning(request, "No active employees found. Please add active employees before creating a payroll run.")
                return redirect('accounts_easy:employee_list')
            
            for employee in employees:
                try:
                    # Calculate basic pay (assuming monthly salary)
                    basic_pay = employee.basic_salary
                    
                    # Calculate bonuses for this employee for the payroll period
                    try:
                        payroll_month = timezone.datetime.strptime(end_date, '%Y-%m-%d').month
                        payroll_year = timezone.datetime.strptime(end_date, '%Y-%m-%d').year
                    except (ValueError, TypeError):
                        payroll_month = timezone.now().month
                        payroll_year = timezone.now().year
                    
                    # Get pending bonuses for this month/year
                    pending_bonuses = EmployeeBonus.objects.filter(
                        employee=employee,
                        month=payroll_month,
                        year=payroll_year,
                        is_applied=False
                    )
                    
                    bonus_amount = sum(bonus.amount for bonus in pending_bonuses)
                    bonus_amount = Decimal(str(bonus_amount))
                    gross_pay = basic_pay + bonus_amount
                    
                    # Calculate tax deductions based on payroll configuration
                    # Convert division results to Decimal to avoid float mixing
                    paye_threshold_monthly = payroll_config.paye_threshold / Decimal('12')
                    paye_tax = max(Decimal('0.00'), (gross_pay - paye_threshold_monthly) * payroll_config.paye_rate)
                    
                    nis_ceiling_monthly = payroll_config.nis_ceiling / Decimal('12')
                    nis_deduction = min(gross_pay * payroll_config.nis_rate, nis_ceiling_monthly)
                    
                    nht_deduction = gross_pay * payroll_config.nht_rate
                    heart_deduction = gross_pay * payroll_config.heart_rate
                    ed_deduction = gross_pay * payroll_config.ed_rate
                    
                    # Create payslip
                    payslip = Payslip.objects.create(
                        employee=employee,
                        payroll_run=payroll_run,
                        basic_pay=basic_pay,
                        bonus=bonus_amount,
                        paye_tax=paye_tax,
                        nis_deduction=nis_deduction,
                        nht_deduction=nht_deduction,
                        heart_deduction=heart_deduction,
                        ed_deduction=ed_deduction
                        # Let the model's save() method calculate gross_pay, total_deductions, and net_pay
                    )
                    
                    # Mark bonuses as applied
                    for bonus in pending_bonuses:
                        bonus.is_applied = True
                        bonus.applied_date = timezone.now()
                        bonus.save()
                    
                    # Update YTD records
                    try:
                        year = timezone.datetime.strptime(end_date, '%Y-%m-%d').year
                    except (ValueError, TypeError):
                        year = timezone.now().year
                    
                    ytd_record, created = EmployeeYTD.objects.get_or_create(
                        employee=employee,
                        year=year
                    )
                    if hasattr(ytd_record, 'update_from_payslip'):
                        ytd_record.update_from_payslip(payslip)
                    
                    payslips_created += 1
                    
                except Exception as e:
                    error_msg = f"Error creating payslip for {employee.full_name}: {str(e)}"
                    errors.append(error_msg)
                    continue
            
            # Update payroll run status
            payroll_run.status = 'completed'
            payroll_run.save()
            
            # Provide feedback to user
            if payslips_created > 0:
                success_msg = f"Payroll run created successfully! Generated {payslips_created} payslips for active employees."
                if errors:
                    success_msg += f" Note: {len(errors)} errors occurred during processing."
                messages.success(request, success_msg)
                
                # Display any errors that occurred
                for error in errors[:3]:  # Show only first 3 errors to avoid message overflow
                    messages.warning(request, error)
                if len(errors) > 3:
                    messages.warning(request, f"...and {len(errors) - 3} more errors. Check the admin panel for details.")
            else:
                messages.error(request, "No payslips were created. Please check that you have active employees and valid payroll configuration.")
                
            return redirect('accounts_easy:payroll_run_detail', payroll_run_id=payroll_run.id)
            
        except Exception as e:
            messages.error(request, f"Error creating payroll run: {str(e)}")
    
    # Ensure 'business' is defined for the context
    business = get_user_business(request.user)
    context = {
        'business': business,
        'today': timezone.now().date()
    }
    return render(request, 'accounts_easy/create_payroll_run.html', context)


@login_required
def payroll_run_detail(request, payroll_run_id):
    """
    View details of a specific payroll run.
    """
    business = get_user_business(request.user)
    if not business:
        messages.error(request, "You don't have access to any approved business.")
        return redirect('accounts_easy:dashboard')
    
    payroll_run = get_object_or_404(PayrollRun, id=payroll_run_id, business=business)
    payslips = Payslip.objects.filter(payroll_run=payroll_run).select_related('employee')
    
    # Calculate totals
    totals = payslips.aggregate(
        total_gross_pay=Sum('gross_pay'),
        total_net_pay=Sum('net_pay'),
        total_deductions=Sum('total_deductions'),
        total_paye=Sum('paye_tax'),
        total_nis=Sum('nis_deduction'),
        total_nht=Sum('nht_deduction')
    )
    
    context = {
        'business': business,
        'payroll_run': payroll_run,
        'payslips': payslips,
        'totals': totals
    }
    return render(request, 'accounts_easy/payroll_run_detail.html', context)


@login_required
def payslip_detail(request, payslip_id):
    """
    View individual payslip details.
    """
    business = get_user_business(request.user)
    if not business:
        messages.error(request, "You don't have access to any approved business.")
        return redirect('accounts_easy:dashboard')
    
    payslip = get_object_or_404(Payslip, id=payslip_id, employee__business=business)
    
    context = {
        'business': business,
        'payslip': payslip,
        'employee': payslip.employee,
        'payroll_run': payslip.payroll_run
    }
    return render(request, 'accounts_easy/payslip_detail.html', context)


@login_required
def print_payslip(request, payslip_id):
    """
    Print-friendly view of payslip.
    """
    business = get_user_business(request.user)
    if not business:
        messages.error(request, "You don't have access to any approved business.")
        return redirect('accounts_easy:dashboard')
    
    payslip = get_object_or_404(Payslip, id=payslip_id, employee__business=business)
    
    context = {
        'business': business,
        'payslip': payslip,
        'employee': payslip.employee,
        'payroll_run': payslip.payroll_run
    }
    return render(request, 'accounts_easy/print_payslip.html', context)


@login_required
def employee_payslips(request, employee_id):
    """
    View all payslips for a specific employee.
    """
    business = get_user_business(request.user)
    if not business:
        messages.error(request, "You don't have access to any approved business.")
        return redirect('accounts_easy:dashboard')
    
    employee = get_object_or_404(Employee, id=employee_id, business=business)
    payslips = Payslip.objects.filter(employee=employee).select_related('payroll_run').order_by('-payroll_run__end_date')
    
    context = {
        'business': business,
        'employee': employee,
        'payslips': payslips
    }
    return render(request, 'accounts_easy/employee_payslips.html', context)

@login_required
def business_settings(request):
    """
    View and update business settings.
    """
    business = get_user_business(request.user)
    if not business:
        messages.error(request, "You don't have access to any approved business.")
        return redirect('accounts_easy:dashboard')
    
    if request.method == 'POST':
        # Update business information
        business.name = request.POST.get('name', business.name)
        business.registration_number = request.POST.get('registration_number', business.registration_number)
        business.address = request.POST.get('address', business.address)
        business.phone = request.POST.get('phone', business.phone)
        business.email = request.POST.get('email', business.email)
        business.tax_id = request.POST.get('tax_id', business.tax_id)
        
        try:
            business.save()
            messages.success(request, "Business settings updated successfully!")
        except Exception as e:
            messages.error(request, f"Error updating business settings: {str(e)}")
    
    context = {
        'business': business
    }
    return render(request, 'accounts_easy/business_settings.html', context)


@login_required
def business_info(request):
    """
    View detailed business information.
    """
    business = get_user_business(request.user)
    if not business:
        messages.error(request, "You don't have access to any approved business.")
        return redirect('accounts_easy:dashboard')
    
    # Get stats for the business info page
    total_employees = Employee.objects.filter(business=business).count()
    active_employees = Employee.objects.filter(business=business, is_active=True).count()
    total_payroll_runs = PayrollRun.objects.filter(business=business).count()
    
    # Get business users (team members)
    business_users = BusinessUser.objects.filter(business=business).select_related('user')
    
    context = {
        'business': business,
        'total_employees': total_employees,
        'active_employees': active_employees,
        'total_payroll_runs': total_payroll_runs,
        'business_users': business_users,
    }
    return render(request, 'accounts_easy/business_info.html', context)


# =============================================================================
# BONUS MANAGEMENT VIEWS
# =============================================================================

@login_required
def bonus_management(request):
    """
    Main bonus management interface.
    """
    business = get_user_business(request.user)
    if not business:
        messages.error(request, "You don't have access to any approved business.")
        return redirect('accounts_easy:dashboard')
    
    # Get all active employees with their current month bonuses
    employees = Employee.objects.filter(business=business, is_active=True).prefetch_related('bonuses')
    current_month = timezone.now().month
    current_year = timezone.now().year
    
    # Calculate stats
    total_current_bonuses = EmployeeBonus.objects.filter(
        employee__business=business,
        month=current_month,
        year=current_year,
        is_applied=False
    ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
    
    active_bonuses_count = EmployeeBonus.objects.filter(
        employee__business=business,
        month=current_month,
        year=current_year,
        is_applied=False
    ).count()
    
    context = {
        'business': business,
        'employees': employees,
        'current_month': current_month,
        'current_year': current_year,
        'total_current_bonuses': total_current_bonuses,
        'active_bonuses_count': active_bonuses_count,
    }
    return render(request, 'accounts_easy/bonus_management.html', context)


@login_required
def employee_bonuses(request, employee_id):
    """
    Manage bonuses for a specific employee.
    """
    business = get_user_business(request.user)
    if not business:
        messages.error(request, "You don't have access to any approved business.")
        return redirect('accounts_easy:dashboard')
    
    employee = get_object_or_404(Employee, id=employee_id, business=business)
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'add_bonus':
            bonus_type = request.POST.get('bonus_type')
            amount = request.POST.get('amount')
            month = request.POST.get('month')
            year = request.POST.get('year')
            description = request.POST.get('description', '')
            is_taxable = request.POST.get('is_taxable') == 'on'
            
            try:
                amount = Decimal(amount)
                month = int(month)
                year = int(year)
                
                # Check if bonus already exists for this employee, type, month, and year
                existing_bonus = EmployeeBonus.objects.filter(
                    employee=employee,
                    bonus_type=bonus_type,
                    month=month,
                    year=year
                ).first()
                
                if existing_bonus:
                    messages.error(request, f"A {bonus_type} bonus already exists for {employee.full_name} in {month}/{year}.")
                else:
                    EmployeeBonus.objects.create(
                        employee=employee,
                        bonus_type=bonus_type,
                        amount=amount,
                        month=month,
                        year=year,
                        description=description,
                        is_taxable=is_taxable,
                        created_by=request.user
                    )
                    messages.success(request, f"Bonus added successfully for {employee.full_name}!")
                    
            except (ValueError, InvalidOperation) as e:
                messages.error(request, f"Invalid input: {str(e)}")
            except Exception as e:
                messages.error(request, f"Error adding bonus: {str(e)}")
        
        elif action == 'delete_bonus':
            bonus_id = request.POST.get('bonus_id')
            try:
                bonus = EmployeeBonus.objects.get(id=bonus_id, employee=employee)
                if bonus.is_applied:
                    messages.error(request, "Cannot delete a bonus that has already been applied to a payroll run.")
                else:
                    bonus.delete()
                    messages.success(request, "Bonus deleted successfully!")
            except EmployeeBonus.DoesNotExist:
                messages.error(request, "Bonus not found.")
            except Exception as e:
                messages.error(request, f"Error deleting bonus: {str(e)}")
    
    # Get all bonuses for this employee
    bonuses = EmployeeBonus.objects.filter(employee=employee).order_by('-year', '-month', '-created_at')
    
    # Calculate totals
    total_bonuses = bonuses.aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
    current_year = timezone.now().year
    current_month = timezone.now().month
    current_month_bonuses = bonuses.filter(month=current_month, year=current_year)
    
    context = {
        'business': business,
        'employee': employee,
        'bonuses': bonuses,
        'current_month_bonuses': current_month_bonuses,
        'total_bonuses': total_bonuses,
        'current_month': current_month,
        'current_year': current_year,
        'bonus_types': EmployeeBonus.BONUS_TYPE_CHOICES,
        'months': [
            (1, 'January'), (2, 'February'), (3, 'March'), (4, 'April'),
            (5, 'May'), (6, 'June'), (7, 'July'), (8, 'August'),
            (9, 'September'), (10, 'October'), (11, 'November'), (12, 'December')
        ],
        'years': [current_year - 1, current_year, current_year + 1],
    }
    return render(request, 'accounts_easy/employee_bonuses.html', context)


@login_required 
def delete_bonus(request, bonus_id):
    """
    Delete a specific bonus (with confirmation).
    """
    business = get_user_business(request.user)
    if not business:
        messages.error(request, "You don't have access to any approved business.")
        return redirect('accounts_easy:dashboard')
    
    bonus = get_object_or_404(EmployeeBonus, id=bonus_id, employee__business=business)
    
    if request.method == 'POST':
        if bonus.is_applied:
            messages.error(request, "Cannot delete a bonus that has already been applied to a payroll run.")
        else:
            employee_id = bonus.employee.id
            bonus.delete()
            messages.success(request, "Bonus deleted successfully!")
            return redirect('accounts_easy:employee_bonuses', employee_id=employee_id)
    
    context = {
        'business': business,
        'bonus': bonus,
    }
    return render(request, 'accounts_easy/delete_bonus.html', context)