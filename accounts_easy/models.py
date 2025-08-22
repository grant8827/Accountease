from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator
from decimal import Decimal


class Business(models.Model):
    """
    Model representing a business that uses the payroll system.
    """
    STATUS_CHOICES = [
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
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']
        verbose_name_plural = "Businesses"

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
        unique_together = ['business', 'employee_id']
        ordering = ['last_name', 'first_name']

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.employee_id})"

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"


class Deduction(models.Model):
    """
    Model for defining payroll deductions.
    """
    DEDUCTION_TYPE_CHOICES = [
        ('fixed', 'Fixed Amount'),
        ('percentage', 'Percentage'),
    ]
    
    business = models.ForeignKey(Business, on_delete=models.CASCADE, related_name='deductions')
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    deduction_type = models.CharField(max_length=10, choices=DEDUCTION_TYPE_CHOICES)
    amount = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    is_mandatory = models.BooleanField(default=False)
    is_taxable = models.BooleanField(default=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['business', 'name']
        ordering = ['name']

    def __str__(self):
        return f"{self.name} - {self.business.name}"


class PayrollConfiguration(models.Model):
    """
    Model for storing payroll configuration settings.
    """
    FREQUENCY_CHOICES = [
        ('weekly', 'Weekly'),
        ('bi_weekly', 'Bi-Weekly'),
        ('monthly', 'Monthly'),
        ('quarterly', 'Quarterly'),
        ('annually', 'Annually'),
    ]
    
    business = models.OneToOneField(Business, on_delete=models.CASCADE, related_name='payroll_config')
    pay_frequency = models.CharField(max_length=20, choices=FREQUENCY_CHOICES, default='monthly')
    tax_rate = models.DecimalField(max_digits=5, decimal_places=4, default=Decimal('0.30'))
    overtime_rate = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('1.50'))
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Payroll Config - {self.business.name}"


class PayrollReport(models.Model):
    """
    Model for storing payroll reports.
    """
    business = models.ForeignKey(Business, on_delete=models.CASCADE, related_name='payroll_reports')
    report_name = models.CharField(max_length=200)
    pay_period_start = models.DateField()
    pay_period_end = models.DateField()
    total_gross_pay = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_deductions = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_net_pay = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-pay_period_start']

    def __str__(self):
        return f"{self.report_name} ({self.pay_period_start} - {self.pay_period_end})"


class EmployeeYTD(models.Model):
    """
    Model for tracking employee year-to-date information.
    """
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='ytd_records')
    year = models.IntegerField()
    gross_pay = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_deductions = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    net_pay = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    tax_withheld = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['employee', 'year']
        ordering = ['-year']

    def __str__(self):
        return f"{self.employee.full_name} - {self.year} YTD"


class EmployeeBonus(models.Model):
    """
    Model for managing employee bonuses.
    """
    BONUS_TYPE_CHOICES = [
        ('performance', 'Performance Bonus'),
        ('holiday', 'Holiday Bonus'),
        ('signing', 'Signing Bonus'),
        ('retention', 'Retention Bonus'),
        ('project', 'Project Bonus'),
        ('other', 'Other'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('paid', 'Paid'),
        ('cancelled', 'Cancelled'),
    ]
    
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='bonuses')
    bonus_type = models.CharField(max_length=20, choices=BONUS_TYPE_CHOICES)
    amount = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    description = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    approved_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='approved_bonuses'
    )
    approved_at = models.DateTimeField(null=True, blank=True)
    paid_at = models.DateTimeField(null=True, blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.employee.full_name} - {self.get_bonus_type_display()} - ${self.amount}"

    @property
    def is_approved(self):
        return self.status == 'approved'

    @property
    def is_paid(self):
        return self.status == 'paid'

    @property
    def can_be_paid(self):
        return self.status == 'approved'
