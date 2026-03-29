#!/usr/bin/env python
import os
import sys
import django

# Add the project path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'SmartCareSystem.settings')
django.setup()

from django.contrib.auth import get_user_model
from billing.models import Bill, Payment
from django.utils import timezone
import uuid

def create_payment():
    """Create a payment directly"""
    try:
        # Get current user and bill
        User = get_user_model()
        user = User.objects.first()
        bill = Bill.objects.get(id=18)  # Bill with remaining balance
        
        print(f'User: {user.email}')
        print(f'Bill: #{bill.id}')
        
        # Calculate remaining balance
        paid_amount = sum(p.amount for p in bill.payments.filter(status='completed'))
        remaining_balance = bill.total_amount - paid_amount
        
        print(f'Remaining Balance: Rs. {remaining_balance}')
        
        if remaining_balance > 0:
            # Create payment
            payment = Payment.objects.create(
                bill=bill,
                amount=remaining_balance,
                payment_method='cash',
                transaction_id=f'TXN-{uuid.uuid4().hex[:12].upper()}',
                status='completed',
                paid_date=timezone.now(),
                notes=f'Direct payment by {user.email}'
            )
            
            print(f'✅ Payment Created: #{payment.id}')
            print(f'✅ Amount: Rs. {payment.amount}')
            print(f'✅ Method: {payment.payment_method}')
            print(f'✅ Status: {payment.status}')
            print(f'✅ Transaction ID: {payment.transaction_id}')
            
            # Update bill status
            total_paid = sum(p.amount for p in bill.payments.filter(status='completed'))
            if total_paid >= bill.total_amount:
                bill.status = 'paid'
                bill.save()
                print(f'✅ Bill marked as paid')
            
            print('')
            print('🎉 PAYMENT SUCCESSFULLY CREATED!')
            print('You can now check your payment history to see this payment.')
            print('Go to: http://127.0.0.1:8000/billing/payments/')
            
        else:
            print('❌ Bill is already fully paid')
            
    except Exception as e:
        print(f'❌ Error: {str(e)}')
        import traceback
        print(f'Traceback: {traceback.format_exc()}')

if __name__ == '__main__':
    create_payment()
