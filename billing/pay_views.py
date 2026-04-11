from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from billing.models import Bill, Payment
import uuid

VALID_METHODS = ('cash', 'esewa', 'khalti', 'bank_transfer')

METHOD_DISPLAY = {
    'cash': 'Cash Payment',
    'esewa': 'eSewa Digital Wallet',
    'khalti': 'Khalti Mobile Payment',
    'bank_transfer': 'Bank Transfer',
}


def _bill_pay_permission_denied(request, bill):
    if request.user.is_patient and bill.patient != request.user:
        messages.error(request, 'You can only pay your own bills.')
        return True
    if request.user.is_doctor and bill.doctor != request.user:
        messages.error(request, 'You can only process payments for your own bills.')
        return True
    if not (request.user.is_patient or request.user.is_doctor or request.user.is_admin):
        messages.error(request, 'You are not allowed to pay this bill.')
        return True
    return False


@login_required
def pay_view(request, bill_id):
    """
    Two-step payment: choose method → confirm → complete.
    """
    try:
        bill = Bill.objects.get(id=bill_id)

        if _bill_pay_permission_denied(request, bill):
            return redirect('billing:bill_list')

        paid = sum(p.amount for p in bill.payments.filter(status='completed'))
        remaining = bill.total_amount - paid

        if remaining <= 0:
            messages.error(request, 'Bill already paid')
            return redirect('billing:bill_list')

        if request.method == 'POST':
            method = request.POST.get('payment_method', 'cash')
            if method not in VALID_METHODS:
                method = 'cash'

            # Step 2: user confirmed on the review screen
            if request.POST.get('confirmed') == 'yes':
                payment = Payment.objects.create(
                    bill=bill,
                    amount=remaining,
                    payment_method=method,
                    transaction_id=f"TXN-{uuid.uuid4().hex[:12].upper()}",
                    status='completed',
                    paid_date=timezone.now(),
                    notes=f"Payment via {method}",
                )

                total_paid = sum(p.amount for p in bill.payments.filter(status='completed'))
                if total_paid >= bill.total_amount:
                    bill.status = 'paid'
                    bill.save()

                messages.success(request, f'Payment of Rs. {payment.amount} processed successfully!')
                return redirect(
                    'billing:payment_success_with_details',
                    payment_id=payment.id,
                    method=method,
                    amount=payment.amount,
                    transaction_id=payment.transaction_id,
                )

            # Step 1: review & confirm screen
            if request.POST.get('payment_preview') == '1':
                return render(
                    request,
                    'billing/pay_confirm.html',
                    {
                        'bill': bill,
                        'remaining_balance': remaining,
                        'payment_method': method,
                        'method_label': METHOD_DISPLAY.get(method, 'Payment'),
                    },
                )

        return render(
            request,
            'billing/pay.html',
            {'bill': bill, 'remaining_balance': remaining},
        )

    except Bill.DoesNotExist:
        messages.error(request, 'Bill not found')
        return redirect('billing:bill_list')
    except Exception as e:
        messages.error(request, f'Error: {str(e)}')
        return redirect('billing:bill_list')

@login_required
def payment_success_with_details_view(request, payment_id, method, amount, transaction_id):
    """
    Payment success page with details
    """
    try:
        # Get payment details
        payment = Payment.objects.get(id=payment_id)
        
        # Method display mapping
        method_display = {
            'cash': 'Cash Payment',
            'esewa': 'eSewa Digital Wallet',
            'khalti': 'Khalti Mobile Payment',
            'bank_transfer': 'Bank Transfer'
        }
        
        method_name = method_display.get(method, 'Payment')
        
        context = {
            'payment': payment,
            'method_display': method_name,
            'amount': amount,
            'transaction_id': transaction_id,
            'payment_time': payment.paid_date.strftime('%I:%M %p')
        }
        
        return render(request, 'billing/payment_success_with_details.html', context)
        
    except Payment.DoesNotExist:
        messages.error(request, 'Payment not found')
        return redirect('billing:bill_list')
    except Exception as e:
        messages.error(request, f'Error: {str(e)}')
        return redirect('billing:bill_list')
