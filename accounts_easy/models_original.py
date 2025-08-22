from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.contrib.auth.models import User


from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.contrib.auth.models import User
from decimal import Decimal


class Business(models.Model):

    """
    Model representing a business that uses the payroll system.
    """
    name = models.CharField(max_length=255)
    registration_number = models.CharField(max_length=100, blank=True, null=True)
    address = models.CharField(max_length=255, blank=True)
    phone = models.CharField(max_length=50, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    tax_id = models.CharField(max_length=100, blank=True, null=True)
    status = models.CharField(
        max_length=20,
        choices=[('pending', 'Pending'), ('approved', 'Approved'), ('rejected', 'Rejected')],
        default='pending'
    )
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='owned_businesses')
    created_at = models.DateTimeField(auto_now_add=True)


    def __str__(self):
        return self.name

    @property
    def is_approved(self):
        """Check if business is approved for operation."""
        return self.status == 'approved'
    
    @property
    def can_operate(self):
        """Check if business can perform payroll operations."""
        return self.is_approved


class Transaction(models.Model):
    """
    Model for recording income and expenditure transactions.
    """
    TRANSACTION_TYPE_CHOICES = [
        ('income', 'Income'),
        ('expenditure', 'Expenditure'),
    ]

    business = models.ForeignKey(Business, on_delete=models.CASCADE, related_name='transactions')
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPE_CHOICES)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    description = models.CharField(max_length=255)
    date = models.DateField()
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date', '-created_at']

    def __str__(self):
        return f"{self.get_transaction_type_display()} - {self.amount} on {self.date}"

class Transaction(models.Model):
    """
    Model for recording income and expenditure transactions.
    """
    TRANSACTION_TYPE_CHOICES = [
        ('income', 'Income'),
        ('expenditure', 'Expenditure'),
    ]

    business = models.ForeignKey(Business, on_delete=models.CASCADE, related_name='transactions')
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPE_CHOICES)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    description = models.CharField(max_length=255)
    date = models.DateField()
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date', '-created_at']


    """
    Model representing a business that uses the payroll system.
    """
    APPROVAL_STATUS_CHOICES = [
        ('pending', 'Pending Approval'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]
    
    name = models.CharField(max_length=200)
    registration_number = models.CharField(max_length=50, unique=True, blank=True)
    address = models.TextField()
    phone = models.CharField(max_length=20, blank=True)
    email = models.EmailField()
    tax_id = models.CharField(max_length=50, blank=True)
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='owned_businesses')
    is_active = models.BooleanField(default=True)
    approval_status = models.CharField(max_length=20, choices=APPROVAL_STATUS_CHOICES, default='pending')
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_businesses')
    approved_at = models.DateTimeField(null=True, blank=True)
    rejection_reason = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']
        verbose_name_plural = "Businesses"

    def __str__(self):
        return f"{self.name} ({self.get_status_display()})"
    
    @property
    def is_approved(self):
        """Check if business is approved for operation."""
        return self.status == 'approved'
    
    @property
    def can_operate(self):
        """Check if business can perform payroll operations."""
        return self.is_active and self.is_approved

class Transaction(models.Model):
    """
    Model for recording income and expenditure transactions.
    """
    TRANSACTION_TYPE_CHOICES = [
        ('income', 'Income'),
        ('expenditure', 'Expenditure'),
    ]

    business = models.ForeignKey(Business, on_delete=models.CASCADE, related_name='transactions')
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPE_CHOICES)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    description = models.CharField(max_length=255)
    date = models.DateField()
    created_by = models.ForeignKey('auth.User', on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date', '-created_at']

    def __str__(self):
        return f"{self.get_transaction_type_display()} - {self.amount} on {self.date}"


class BusinessUser(models.Model):
    """
    Model for managing user access to businesses with roles.
    """
    ROLE_CHOICES = [
        ('owner', 'Owner'),
        ('manager', 'Manager'),
        ('hr', 'HR Staff'),
        ('accountant', 'Accountant'),
        ('viewer', 'Viewer'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    business = models.ForeignKey(Business, on_delete=models.CASCADE)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['user', 'business']
        ordering = ['business__name', 'user__username']

    def __str__(self):
        return f"{self.user.username} - {self.business.name} ({self.role})"


class Employee(models.Model):
    """
    Model representing an employee in the payroll system.
    """
    business = models.ForeignKey(Business, on_delete=models.CASCADE, related_name='employees')
    employee_id = models.CharField(max_length=20, help_text="Unique employee identifier")
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    email = models.EmailField()
    phone = models.CharField(max_length=20, blank=True)
    job_title = models.CharField(max_length=100)
    basic_salary = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    date_of_hire = models.DateField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['last_name', 'first_name']
        unique_together = ['business', 'employee_id']
        
    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.employee_id}) - {self.business.name}"

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"


class DeductionType(models.Model):
    """
    Model representing types of deductions that can be applied to employees.
    """
    business = models.ForeignKey(Business, on_delete=models.CASCADE, related_name='deduction_types')
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    is_percentage = models.BooleanField(default=False, help_text="Is this deduction calculated as a percentage?")
    default_value = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        default=0.00,
        help_text="Default amount or percentage"
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']
        unique_together = ['business', 'name']

    def __str__(self):
        return f"{self.name} - {self.business.name}"


class EmployeeDeduction(models.Model):
    """
    Model representing deductions applied to specific employees.
    """
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='deductions')
    deduction_type = models.ForeignKey(DeductionType, on_delete=models.CASCADE)
    amount = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    effective_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-effective_date']
        unique_together = ['employee', 'deduction_type', 'effective_date']

    def __str__(self):
        return f"{self.employee.full_name} - {self.deduction_type.name}"


class TaxSetting(models.Model):
    """
    Model for storing tax rates and settings for different years.
    """
    business = models.ForeignKey(Business, on_delete=models.CASCADE, related_name='tax_settings')
    year = models.IntegerField()
    nis_employee_rate = models.DecimalField(
        max_digits=5, 
        decimal_places=4, 
        default=0.0300,
        help_text="NIS employee rate (e.g., 0.0300 for 3%)"
    )
    nht_employee_rate = models.DecimalField(
        max_digits=5, 
        decimal_places=4, 
        default=0.0200,
        help_text="NHT employee rate (e.g., 0.0200 for 2%)"
    )
    heart_rate = models.DecimalField(
        max_digits=5, 
        decimal_places=4, 
        default=0.0250,
        help_text="HEART rate (e.g., 0.0250 for 2.5%)"
    )
    ed_rate = models.DecimalField(
        max_digits=5, 
        decimal_places=4, 
        default=0.0250,
        help_text="Education rate (e.g., 0.0250 for 2.5%)"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-year']
        unique_together = ['business', 'year']

    def __str__(self):
        return f"Tax Settings {self.year} - {self.business.name}"


class PayrollRun(models.Model):
    """
    Model representing a payroll run for a specific period.
    """
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]
    
    business = models.ForeignKey(Business, on_delete=models.CASCADE, related_name='payroll_runs')
    start_date = models.DateField()
    end_date = models.DateField()
    run_date = models.DateField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-end_date']
        unique_together = ['business', 'start_date', 'end_date']

    def __str__(self):
        return f"Payroll Run {self.start_date} to {self.end_date} - {self.business.name}"


class Payslip(models.Model):
    """
    Model representing individual payslips for employees.
    """
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='payslips')
    payroll_run = models.ForeignKey(PayrollRun, on_delete=models.CASCADE, related_name='payslips')
    basic_pay = models.DecimalField(max_digits=10, decimal_places=2)
    overtime_pay = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    bonus = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    gross_pay = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Tax deductions
    paye_tax = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    nis_deduction = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    nht_deduction = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    heart_deduction = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    ed_deduction = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    
    # Other deductions
    other_deductions = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    total_deductions = models.DecimalField(max_digits=10, decimal_places=2)
    net_pay = models.DecimalField(max_digits=10, decimal_places=2)
    
    generated_date = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-payroll_run__end_date', 'employee__last_name']
        unique_together = ['employee', 'payroll_run']

    def __str__(self):
        return f"{self.employee.full_name} - {self.payroll_run}"

    def save(self, *args, **kwargs):
        # Calculate totals automatically
        self.gross_pay = self.basic_pay + self.overtime_pay + self.bonus
        self.total_deductions = (
            self.paye_tax + self.nis_deduction + self.nht_deduction + 
            self.heart_deduction + self.ed_deduction + self.other_deductions
        )
        self.net_pay = self.gross_pay - self.total_deductions
        super().save(*args, **kwargs)


class PayrollConfiguration(models.Model):
    """
    Model for business-specific payroll configuration settings.
    """
    PAYROLL_FREQUENCY_CHOICES = [
        ('weekly', 'Weekly'),
        ('bi_weekly', 'Bi-Weekly'),
        ('monthly', 'Monthly'),
        ('semi_monthly', 'Semi-Monthly'),
    ]
    
    business = models.OneToOneField(Business, on_delete=models.CASCADE, related_name='payroll_config')
    payroll_frequency = models.CharField(max_length=20, choices=PAYROLL_FREQUENCY_CHOICES, default='monthly')
    
    # Tax Configuration
    paye_rate = models.DecimalField(max_digits=5, decimal_places=4, default=0.25, help_text="PAYE tax rate (e.g., 0.25 for 25%)")
    nis_rate = models.DecimalField(max_digits=5, decimal_places=4, default=0.03, help_text="NIS contribution rate")
    nht_rate = models.DecimalField(max_digits=5, decimal_places=4, default=0.02, help_text="NHT contribution rate")
    heart_rate = models.DecimalField(max_digits=5, decimal_places=4, default=0.003, help_text="HEART contribution rate")
    ed_rate = models.DecimalField(max_digits=5, decimal_places=4, default=0.0025, help_text="Education tax rate")
    
    # Thresholds
    paye_threshold = models.DecimalField(max_digits=10, decimal_places=2, default=1500000, help_text="Annual PAYE threshold")
    nis_ceiling = models.DecimalField(max_digits=10, decimal_places=2, default=5000000, help_text="Annual NIS ceiling")
    
    # Company Information
    company_nis_number = models.CharField(max_length=50, blank=True, help_text="Company NIS registration number")
    company_paye_number = models.CharField(max_length=50, blank=True, help_text="Company PAYE registration number")
    
    # Payroll Settings
    overtime_rate_multiplier = models.DecimalField(max_digits=3, decimal_places=2, default=1.5, help_text="Overtime rate multiplier")
    standard_hours_per_week = models.IntegerField(default=40, help_text="Standard working hours per week")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Payroll Config - {self.business.name}"


class EmployeeYTD(models.Model):
    """
    Model for tracking Year-to-Date earnings and deductions for employees.
    """
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='ytd_records')
    year = models.IntegerField()
    
    # YTD Earnings
    ytd_gross_pay = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    ytd_basic_pay = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    ytd_overtime_pay = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    ytd_bonus = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    
    # YTD Deductions
    ytd_paye_tax = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    ytd_nis_deduction = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    ytd_nht_deduction = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    ytd_heart_deduction = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    ytd_ed_deduction = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    ytd_other_deductions = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    ytd_total_deductions = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    ytd_net_pay = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    
    last_updated = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['employee', 'year']
        ordering = ['-year', 'employee__last_name']
    
    def __str__(self):
        return f"{self.employee.full_name} - YTD {self.year}"
    
    def update_from_payslip(self, payslip):
        """Update YTD totals from a payslip."""
        self.ytd_gross_pay += payslip.gross_pay
        self.ytd_basic_pay += payslip.basic_pay
        self.ytd_overtime_pay += payslip.overtime_pay
        self.ytd_bonus += payslip.bonus
        self.ytd_paye_tax += payslip.paye_tax
        self.ytd_nis_deduction += payslip.nis_deduction
        self.ytd_nht_deduction += payslip.nht_deduction
        self.ytd_heart_deduction += payslip.heart_deduction
        self.ytd_ed_deduction += payslip.ed_deduction
        self.ytd_other_deductions += payslip.other_deductions
        self.ytd_total_deductions += payslip.total_deductions
        self.ytd_net_pay += payslip.net_pay
        self.save()


class EmployeeBonus(models.Model):
    """
    Model for managing monthly bonuses for employees.
    """
    BONUS_TYPE_CHOICES = [
        ('performance', 'Performance Bonus'),
        ('holiday', 'Holiday Bonus'),
        ('attendance', 'Attendance Bonus'),
        ('sales', 'Sales Bonus'),
        ('special', 'Special Recognition'),
        ('other', 'Other'),
    ]
    
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='bonuses')
    bonus_type = models.CharField(max_length=20, choices=BONUS_TYPE_CHOICES, default='performance')
    amount = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    month = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(12)])
    year = models.IntegerField()
    description = models.TextField(blank=True)
    is_taxable = models.BooleanField(default=True, help_text="Is this bonus subject to tax?")
    is_applied = models.BooleanField(default=False, help_text="Has this bonus been applied to a payroll run?")
    applied_date = models.DateTimeField(null=True, blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-year', '-month', 'employee__last_name']
        unique_together = ['employee', 'bonus_type', 'month', 'year']
    
    def __str__(self):
        return f"{self.employee.full_name} - {self.get_bonus_type_display()} - {self.month}/{self.year}: ${self.amount}"
    
    @property
    def month_name(self):
        months = [
            'January', 'February', 'March', 'April', 'May', 'June',
            'July', 'August', 'September', 'October', 'November', 'December'
        ]
        return months[self.month - 1]


class PayrollReport(models.Model):
    """
    Model for storing payroll reports and summaries.
    """
    REPORT_TYPE_CHOICES = [
        ('payroll_summary', 'Payroll Summary'),
        ('tax_report', 'Tax Report'),
        ('ytd_summary', 'YTD Summary'),
        ('employee_summary', 'Employee Summary'),
    ]
    
    business = models.ForeignKey(Business, on_delete=models.CASCADE, related_name='payroll_reports')
    report_type = models.CharField(max_length=20, choices=REPORT_TYPE_CHOICES)
    report_period_start = models.DateField()
    report_period_end = models.DateField()
    
    # Report Data (stored as JSON)
    report_data = models.JSONField(default=dict, help_text="Report data in JSON format")
    
    generated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    generated_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-generated_at']
    
    def __str__(self):
        return f"{self.get_report_type_display()} - {self.business.name} ({self.report_period_start} to {self.report_period_end})"
