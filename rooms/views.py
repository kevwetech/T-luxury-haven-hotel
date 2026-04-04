from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.db.models import Q
from django.utils import timezone
from django.db.models import Sum, Count
from .models import Room, Booking, GalleryImage, Testimonial
from .forms import BookingForm, RoomForm, GalleryImageForm, TestimonialForm
import requests
import hmac
import hashlib
import json
from django.conf import settings


def home(request):
    rooms        = Room.objects.filter(is_active=True)
    testimonials = Testimonial.objects.filter(is_active=True)
    return render(request, 'rooms/home.html', {
        'rooms':        rooms,
        'testimonials': testimonials,
    })

def rooms_page(request):
    rooms = Room.objects.filter(is_active=True)
    return render(request, 'rooms/rooms.html', {'rooms': rooms})



def room_detail(request, pk):
    room = get_object_or_404(Room, pk=pk, is_active=True)
    return render(request, 'rooms/room_detail.html', {'room': room})

def about(request):
    return render(request, 'rooms/about.html')


def gallery(request):
    category = request.GET.get('category', '')
    images   = GalleryImage.objects.filter(is_active=True)
    if category:
        images = images.filter(category=category)
    categories = GalleryImage.CATEGORY_CHOICES
    return render(request, 'rooms/gallery.html', {
        'images':     images,
        'categories': categories,
        'active_cat': category,
    })

def contact(request):
    if request.method == 'POST':
        name    = request.POST.get('name')
        email   = request.POST.get('email')
        message = request.POST.get('message')
        messages.success(request, f'Thank you {name}, we will get back to you shortly.')
        return redirect('contact')
    return render(request, 'rooms/contact.html')



@login_required
def book_room(request, pk):
    room = get_object_or_404(Room, pk=pk, is_active=True)

    if request.method == 'POST':
        form = BookingForm(request.POST)
        if form.is_valid():
            booking = form.save(commit=False)
            booking.user = request.user
            booking.room = room
            booking.status = 'pending'

            errors = []

            if booking.check_in >= booking.check_out:
                errors.append("Check-out date must be after check-in date.")

            if booking.check_in < timezone.now().date():
                errors.append("Check-in date cannot be in the past.")

            overlapping = Booking.objects.filter(
                room=room,
                status__in=['pending', 'confirmed'],
                check_in__lt=booking.check_out,
                check_out__gt=booking.check_in,
            )
            if overlapping.exists():
                errors.append("This room is not available for the selected dates.")

            if errors:
                for error in errors:
                    messages.error(request, error)
                return render(request, 'rooms/book_room.html', {'room': room, 'form': form})

            # Calculate total
            nights = (booking.check_out - booking.check_in).days
            total_price = nights * room.price

            # Save booking as pending (not confirmed yet)
            booking.total_price = total_price
            booking.save()

            # Initialize Paystack transaction
            amount_kobo = int(total_price * 100)  # Paystack uses kobo
            callback_url = request.build_absolute_uri(f'/booking/paystack/callback/?booking_id={booking.pk}')

            headers = {
                'Authorization': f'Bearer {settings.PAYSTACK_SECRET_KEY}',
                'Content-Type': 'application/json',
            }
            payload = {
                'email': request.user.email,
                'amount': amount_kobo,
                'reference': f'booking_{booking.pk}_{booking.created_at.strftime("%Y%m%d%H%M%S")}',
                'callback_url': callback_url,
                'metadata': {
                    'booking_id': booking.pk,
                    'room': str(room),
                    'check_in': str(booking.check_in),
                    'check_out': str(booking.check_out),
                }
            }

            response = requests.post(
                'https://api.paystack.co/transaction/initialize',
                headers=headers,
                json=payload,
            )
            data = response.json()

            if data['status']:
                # Redirect to Paystack payment page
                return redirect(data['data']['authorization_url'])
            else:
                booking.delete()  # Remove pending booking if Paystack fails
                messages.error(request, 'Payment initialization failed. Please try again.')
                return render(request, 'rooms/book_room.html', {'room': room, 'form': form})

    else:
        form = BookingForm()

    return render(request, 'rooms/book_room.html', {'room': room, 'form': form})


@login_required
def paystack_callback(request):
    reference = request.GET.get('reference')
    booking_id = request.GET.get('booking_id')

    if not reference or not booking_id:
        messages.error(request, 'Invalid payment reference.')
        return redirect('my_bookings')

    # Verify payment with Paystack
    headers = {
        'Authorization': f'Bearer {settings.PAYSTACK_SECRET_KEY}',
    }
    response = requests.get(
        f'https://api.paystack.co/transaction/verify/{reference}',
        headers=headers,
    )
    data = response.json()

    if data['status'] and data['data']['status'] == 'success':
        # Confirm the booking
        booking = get_object_or_404(Booking, pk=booking_id, user=request.user)
        booking.status = 'confirmed'
        booking.save()
        messages.success(request, 'Payment successful! Your booking is confirmed.')
        return redirect('my_bookings')
    else:
        # Payment failed — cancel the booking
        booking = get_object_or_404(Booking, pk=booking_id, user=request.user)
        booking.status = 'cancelled'
        booking.save()
        messages.error(request, 'Payment failed. Your booking has been cancelled.')
        return redirect('my_bookings')

    

@login_required
def my_bookings(request):
    bookings = Booking.objects.filter(user=request.user)
    return render(request, 'rooms/my_bookings.html', {'bookings': bookings})


@login_required
def cancel_booking(request, pk):
    booking = get_object_or_404(Booking, pk=pk, user=request.user)
    if booking.status not in ['cancelled']:
        booking.status = 'cancelled'
        booking.save()
        messages.success(request, 'Booking cancelled successfully.')
    return redirect('my_bookings')


# ── DASHBOARD HOME ──
@staff_member_required
def dashboard(request):
    total_bookings  = Booking.objects.count()
    pending         = Booking.objects.filter(status='pending').count()
    confirmed       = Booking.objects.filter(status='confirmed').count()
    cancelled       = Booking.objects.filter(status='cancelled').count()
    total_rooms     = Room.objects.filter(is_active=True).count()
    total_revenue   = Booking.objects.filter(
        status='confirmed'
    ).aggregate(total=Sum('total_price'))['total'] or 0
    recent_bookings = Booking.objects.select_related('user', 'room').order_by('-created_at')[:10]

    context = {
        'total_bookings':  total_bookings,
        'pending':         pending,
        'confirmed':       confirmed,
        'cancelled':       cancelled,
        'total_rooms':     total_rooms,
        'total_revenue':   total_revenue,
        'recent_bookings': recent_bookings,
    }
    return render(request, 'dashboard/home.html', context)


# ── MANAGE BOOKINGS ──
@staff_member_required
def dashboard_bookings(request):
    status   = request.GET.get('status', '')
    bookings = Booking.objects.select_related('user', 'room').order_by('-created_at')
    if status:
        bookings = bookings.filter(status=status)
    return render(request, 'dashboard/bookings.html', {'bookings': bookings, 'status': status})


@staff_member_required
def dashboard_booking_update(request, pk):
    booking = get_object_or_404(Booking, pk=pk)
    action  = request.POST.get('action')
    if action == 'confirm':
        booking.status = 'confirmed'
        messages.success(request, f'Booking #{pk} confirmed.')
    elif action == 'cancel':
        booking.status = 'cancelled'
        messages.success(request, f'Booking #{pk} cancelled.')
    booking.save()
    return redirect('dashboard_bookings')


# ── MANAGE ROOMS ──
@staff_member_required
def dashboard_rooms(request):
    rooms = Room.objects.select_related('room_type').all()
    return render(request, 'dashboard/rooms.html', {'rooms': rooms})


@staff_member_required
def dashboard_room_add(request):
    if request.method == 'POST':
        form = RoomForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, 'Room added successfully.')
            return redirect('dashboard_rooms')
    else:
        form = RoomForm()
    return render(request, 'dashboard/form_room.html', {'form': form, 'action': 'Add'})


@staff_member_required
def dashboard_room_edit(request, pk):
    room = get_object_or_404(Room, pk=pk)
    if request.method == 'POST':
        form = RoomForm(request.POST, request.FILES, instance=room)
        if form.is_valid():
            form.save()
            messages.success(request, 'Room updated successfully.')
            return redirect('dashboard_rooms')
    else:
        form = RoomForm(instance=room)
    return render(request, 'dashboard/form_room.html', {'form': form, 'action': 'Edit', 'room': room})


@staff_member_required
def dashboard_room_delete(request, pk):
    room = get_object_or_404(Room, pk=pk)
    if request.method == 'POST':
        room.delete()
        messages.success(request, 'Room deleted successfully.')
        return redirect('dashboard_rooms')
    return render(request, 'dashboard/room_confirm_delete.html', {'room': room})


# ── GALLERY MANAGEMENT ──
@staff_member_required
def dashboard_gallery(request):
    images = GalleryImage.objects.all()
    return render(request, 'dashboard/gallery.html', {'images': images})


@staff_member_required
def dashboard_gallery_add(request):
    if request.method == 'POST':
        form = GalleryImageForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, 'Image added successfully.')
            return redirect('dashboard_gallery')
    else:
        form = GalleryImageForm()
    return render(request, 'dashboard/gallery_form.html', {'form': form, 'action': 'Add'})


@staff_member_required
def dashboard_gallery_delete(request, pk):
    image = get_object_or_404(GalleryImage, pk=pk)
    if request.method == 'POST':
        image.delete()
        messages.success(request, 'Image deleted.')
        return redirect('dashboard_gallery')
    return render(request, 'dashboard/gallery_confirm_delete.html', {'image': image})


# ── TESTIMONIALS MANAGEMENT ──
@staff_member_required
def dashboard_testimonials(request):
    testimonials = Testimonial.objects.all()
    return render(request, 'dashboard/testimonials.html', {'testimonials': testimonials})


@staff_member_required
def dashboard_testimonial_add(request):
    if request.method == 'POST':
        form = TestimonialForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, 'Testimonial added successfully.')
            return redirect('dashboard_testimonials')
    else:
        form = TestimonialForm()
    return render(request, 'dashboard/testimonial_form.html', {'form': form, 'action': 'Add'})


@staff_member_required
def dashboard_testimonial_edit(request, pk):
    testimonial = get_object_or_404(Testimonial, pk=pk)
    if request.method == 'POST':
        form = TestimonialForm(request.POST, request.FILES, instance=testimonial)
        if form.is_valid():
            form.save()
            messages.success(request, 'Testimonial updated.')
            return redirect('dashboard_testimonials')
    else:
        form = TestimonialForm(instance=testimonial)
    return render(request, 'dashboard/testimonial_form.html', {'form': form, 'action': 'Edit', 'testimonial': testimonial})


@staff_member_required
def dashboard_testimonial_delete(request, pk):
    testimonial = get_object_or_404(Testimonial, pk=pk)
    if request.method == 'POST':
        testimonial.delete()
        messages.success(request, 'Testimonial deleted.')
        return redirect('dashboard_testimonials')
    return render(request, 'dashboard/testimonial_confirm_delete.html', {'testimonial': testimonial})
