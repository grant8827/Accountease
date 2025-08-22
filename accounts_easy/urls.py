from django.urls import path
from . import views

app_name = 'accounts_easy' # Namespace for URLs

urlpatterns = [
    path('', views.home, name='home'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('register/', views.register_user, name='register_user'),
    path('register-business/', views.register_business, name='register_business'),
    path('business_settings/', views.business_settings, name='business_settings'),
    path('business-info/', views.business_info, name='business_info'),
    path('directory/', views.business_directory, name='business_directory'),
    
    # Employee Management
    path('employees/', views.employee_list, name='employee_list'),
    path('employees/add/', views.add_employee, name='add_employee'),
    path('employees/manage/', views.employee_management, name='employee_management'),
    path('employees/edit/<int:employee_id>/', views.edit_employee, name='edit_employee'),
    path('employees/<int:employee_id>/payslips/', views.employee_payslips, name='employee_payslips'),
    path('employees/<int:pk>/', views.employee_detail, name='employee_detail'),
    
    # Bonus Management
    path('bonuses/', views.bonus_management, name='bonus_management'),
    path('employees/<int:employee_id>/bonuses/', views.employee_bonuses, name='employee_bonuses'),
    path('bonuses/<int:bonus_id>/delete/', views.delete_bonus, name='delete_bonus'),
    
    # Payroll Management
    path('payroll/setup/', views.payroll_setup, name='payroll_setup'),
    path('payroll/tax-setup/', views.tax_setup, name='tax_setup'),
    path('payroll/deductions/', views.deduction_setup, name='deduction_setup'),
    path('payroll/reports/', views.payroll_reports, name='payroll_reports'),
    path('payroll/staff-selection/', views.payroll_staff_selection, name='payroll_staff_selection'),
    path('payroll/create-run/', views.create_payroll_run, name='create_payroll_run'),
    path('payroll/runs/<int:payroll_run_id>/', views.payroll_run_detail, name='payroll_run_detail'),
    
    # Payslip Management
    path('payslips/<int:payslip_id>/', views.payslip_detail, name='payslip_detail'),
    path('payslips/<int:payslip_id>/print/', views.print_payslip, name='print_payslip'),
    
    # YTD and Tracking
    path('employees/ytd/', views.employee_ytd, name='employee_ytd'),
    path('employees/ytd/<int:employee_id>/', views.employee_ytd, name='employee_ytd_detail'),
    
    # Transaction Management
    path('transactions/add/', views.add_transaction, name='add_transaction'),
    path('transactions/', views.view_transactions, name='view_transactions'),
    path('transactions/edit/<int:transaction_id>/', views.edit_transaction, name='edit_transaction'),
    path('transactions/delete/<int:transaction_id>/', views.delete_transaction, name='delete_transaction'),

    # Legacy URLs
    path('deductions/', views.deduction_list, name='deduction_list'),
    path('payroll_runs/', views.payroll_run_list, name='payroll_run_list'),
    
    # Admin URLs
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('admin/approve-business/<int:business_id>/', views.approve_business, name='approve_business'),
    path('admin/reject-business/<int:business_id>/', views.reject_business, name='reject_business'),
    path('admin/delete-business/<int:business_id>/', views.delete_business, name='delete_business'),
]