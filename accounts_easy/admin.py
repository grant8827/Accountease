from django.contrib import admin
from .models import (
    Business, BusinessUser, Employee, Transaction, 
    Deduction, PayrollConfiguration, PayrollReport, 
    EmployeeYTD, EmployeeBonus
)

# Register your models here so they appear in the Django admin interface.

@admin.register(Business)
class BusinessAdmin(admin.ModelAdmin):
    list_display = ('name', 'owner', 'status', 'created_at')
    search_fields = ('name', 'owner__username')
    list_filter = ('status', 'created_at')
    ordering = ('name',)

@admin.register(BusinessUser)
class BusinessUserAdmin(admin.ModelAdmin):
    list_display = ('user', 'business', 'role', 'is_active', 'created_at')
    search_fields = ('user__username', 'business__name')
    list_filter = ('role', 'is_active', 'created_at')
    ordering = ('business__name', 'user__username')

@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = ('employee_id', 'first_name', 'last_name', 'business', 'job_title', 'basic_salary', 'date_of_hire', 'is_active')
    search_fields = ('employee_id', 'first_name', 'last_name', 'business__name')
    list_filter = ('business', 'job_title', 'date_of_hire', 'is_active')
    ordering = ('business__name', 'last_name', 'first_name')

@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ('business', 'transaction_type', 'amount', 'description', 'date', 'created_by')
    search_fields = ('business__name', 'description')
    list_filter = ('transaction_type', 'date', 'business')
    ordering = ('-date',)

@admin.register(Deduction)
class DeductionAdmin(admin.ModelAdmin):
    list_display = ('name', 'business', 'deduction_type', 'amount', 'is_mandatory', 'is_active')
    search_fields = ('name', 'business__name')
    list_filter = ('business', 'deduction_type', 'is_mandatory', 'is_active')
    ordering = ('business__name', 'name')

@admin.register(PayrollConfiguration)
class PayrollConfigurationAdmin(admin.ModelAdmin):
    list_display = ('business', 'pay_frequency', 'tax_rate', 'overtime_rate')
    search_fields = ('business__name',)
    list_filter = ('pay_frequency',)

@admin.register(PayrollReport)
class PayrollReportAdmin(admin.ModelAdmin):
    list_display = ('business', 'report_name', 'pay_period_start', 'pay_period_end', 'total_net_pay', 'created_by')
    search_fields = ('business__name', 'report_name')
    list_filter = ('business', 'pay_period_start')
    ordering = ('-pay_period_start',)

@admin.register(EmployeeYTD)
class EmployeeYTDAdmin(admin.ModelAdmin):
    list_display = ('employee', 'year', 'gross_pay', 'total_deductions', 'net_pay')
    search_fields = ('employee__first_name', 'employee__last_name')
    list_filter = ('year', 'employee__business')
    ordering = ('-year', 'employee__last_name')

@admin.register(EmployeeBonus)
class EmployeeBonusAdmin(admin.ModelAdmin):
    list_display = ('employee', 'bonus_type', 'amount', 'status', 'approved_by', 'created_at')
    search_fields = ('employee__first_name', 'employee__last_name', 'description')
    list_filter = ('bonus_type', 'status', 'created_at', 'employee__business')
    ordering = ('-created_at',)