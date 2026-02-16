import razorpay
from decimal import Decimal
from django.conf import settings
from django.shortcuts import render, redirect, get_object_or_404
from .models import Room, Booking
from django.views.decorators.csrf import csrf_exempt
from datetime import datetime   

# Home Page
def home(request):
    return render(request, 'home.html')


# About Page
def about(request):
    return render(request, 'about.html')


# Contact Page
def contact(request):
    return render(request, 'contact.html')


# Banquet Page
def banquet(request):
    return render(request, 'banquet.html')


# Rooms Page
def rooms(request):
    all_rooms = Room.objects.all()
    return render(request, 'room.html', {'rooms': all_rooms})

def checkout(request):
    if request.method == "POST":
        room_slug = request.POST.get('room_type')
        room = get_object_or_404(Room, slug=room_slug)

        # Booking info from form
        check_in_date = request.POST.get('check_in_date')
        check_in_time = request.POST.get('check_in_time')
        check_out_date = request.POST.get('check_out_date')
        check_out_time = request.POST.get('check_out_time')
        adults = int(request.POST.get('adults', 1))
        children = int(request.POST.get('children', 0))
        rooms_count = int(request.POST.get('rooms', 1))

        check_in = datetime.strptime(check_in_date, "%Y-%m-%d")
        check_out = datetime.strptime(check_out_date, "%Y-%m-%d")
        no_of_days = (check_out - check_in).days
        if no_of_days <= 0:
            no_of_days = 1

        subtotal = room.price * rooms_count * no_of_days
        tax = subtotal * Decimal('0.12')
        total = subtotal + tax

        # Save all checkout info in session
        request.session['checkout_data'] = {
            "room_id": room.id,
            "room_name": room.title,
            "check_in_date": check_in_date,
            "check_in_time": check_in_time,
            "check_out_date": check_out_date,
            "check_out_time": check_out_time,
            "adults": adults,
            "children": children,
            "rooms_count": rooms_count,
            "no_of_days": no_of_days,
            "subtotal": str(subtotal),
            "tax": str(tax),
            "total": str(total),
        }

        context = {
            **request.session['checkout_data']
        }
        return render(request, 'checkout.html', context)

    return redirect('rooms')

def payment(request):
    if request.method == "POST":
        # Get room/payment info
        checkout_data = request.session.get('checkout_data')
        if not checkout_data:
            return redirect('checkout')

        name = request.POST.get('name')
        email = request.POST.get('email')
        phone = request.POST.get('phone')
        total = Decimal(checkout_data['total'])
        amount_paise = int(total * 100)

        client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))

        # Create Payment Link
        payment_link = client.payment_link.create({
            "amount": amount_paise,
            "currency": "INR",
            "accept_partial": False,
            "customer": {
                "name": name,
                "email": email,
                "contact": phone
            },
            "notify": {"sms": True, "email": True},
            "reminder_enable": True,
            "callback_url": request.build_absolute_uri('/payment/success/'),
            "callback_method": "get"
        })

        # Save booking + payment info in session
        request.session['booking_data'] = {
            **checkout_data,
            "name": name,
            "email": email,
            "phone": phone,
        }

        return redirect(payment_link['short_url'])

    return redirect('checkout')

@csrf_exempt
def payment_success(request):
    booking_data = request.session.get('booking_data')
    if not booking_data:
        return render(request, "payment_failed.html", {"message": "Booking data not found in session."})

    try:
        payment_id = request.GET.get('razorpay_payment_id')
        if not payment_id:
            return render(request, "payment_failed.html", {"message": "Payment ID not found."})

        client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
        payment = client.payment.fetch(payment_id)

        if payment['status'] == 'authorized':
            client.payment.capture(payment_id, payment['amount'])
            payment = client.payment.fetch(payment_id)

        if payment['status'] != 'captured':
            return render(request, "payment_failed.html", {"message": f"Payment status: {payment['status']}"})

        room = get_object_or_404(Room, id=booking_data['room_id'])

        booking = Booking.objects.create(
            room=room,
            name=booking_data['name'],
            email=booking_data['email'],
            phone=booking_data['phone'],
            total=Decimal(booking_data['total']),
            payment_status='paid',
            check_in_date=booking_data['check_in_date'],
            check_out_date=booking_data['check_out_date'],
            check_in_time=booking_data.get('check_in_time'),
            check_out_time=booking_data.get('check_out_time'),
            adults=booking_data.get('adults'),
            children=booking_data.get('children'),
            rooms_count=booking_data.get('rooms_count'),
            subtotal=Decimal(booking_data.get('subtotal')),
            tax=Decimal(booking_data.get('tax'))
        )

        # Clear session
        del request.session['booking_data']
        del request.session['checkout_data']

        return render(request, "payment_success.html", {"booking": booking})

    except Exception as e:
        print("Payment processing error:", e)
        return render(request, "payment_failed.html", {"message": str(e)})
