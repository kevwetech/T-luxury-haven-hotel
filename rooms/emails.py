import os
import sendgrid
from sendgrid.helpers.mail import Mail
from django.conf import settings


# ── HELPER ───────────────────────────────────────────────

def send_email(to_email, subject, body):
    """Send email via SendGrid HTTP API — bypasses SMTP port restrictions."""
    sg = sendgrid.SendGridAPIClient(
        api_key=os.environ.get('SENDGRID_API_KEY')
    )
    message = Mail(
        from_email         = settings.DEFAULT_FROM_EMAIL,
        to_emails          = to_email,
        subject            = subject,
        plain_text_content = body,
    )
    response = sg.send(message)
    return response


# ── BOOKING EMAILS ────────────────────────────────────────

def email_admin_new_booking(booking):
    """Email admin when a user makes a new booking."""
    nights = (booking.check_out - booking.check_in).days
    send_email(
        to_email = os.environ.get('ADMIN_EMAIL', settings.DEFAULT_FROM_EMAIL),
        subject  = f'New Booking #{booking.pk} — Room {booking.room.room_number}',
        body     = (
            f'A new booking has been made.\n\n'
            f'--- BOOKING DETAILS ---\n'
            f'Booking ID : #{booking.pk}\n'
            f'Guest      : {booking.user.username} ({booking.user.email})\n'
            f'Room       : {booking.room.room_number} — {booking.room.room_type}\n'
            f'Check-in   : {booking.check_in}\n'
            f'Check-out  : {booking.check_out}\n'
            f'Nights     : {nights}\n'
            f'Guests     : {booking.guests}\n'
            f'Total      : ${booking.total_price}\n'
            f'Status     : {booking.status.upper()}\n\n'
            f'Log in to the dashboard to confirm or cancel:\n'
            f'{settings.SITE_URL}/dashboard/bookings/\n\n'
            f'— T-Luxury Haven Booking System'
        ),
    )


def email_user_booking_confirmed(booking):
    """Email user when their booking is confirmed by admin."""
    nights = (booking.check_out - booking.check_in).days
    send_email(
        to_email = booking.user.email,
        subject  = 'Booking Confirmed — T-Luxury Haven Hotel',
        body     = (
            f'Dear {booking.user.first_name or booking.user.username},\n\n'
            f'Great news! Your booking has been confirmed.\n\n'
            f'--- YOUR RESERVATION ---\n'
            f'Booking ID : #{booking.pk}\n'
            f'Room       : {booking.room.room_number} — {booking.room.room_type}\n'
            f'Check-in   : {booking.check_in} (from 3:00 PM)\n'
            f'Check-out  : {booking.check_out} (by 12:00 PM)\n'
            f'Nights     : {nights}\n'
            f'Guests     : {booking.guests}\n'
            f'Total      : ${booking.total_price}\n\n'
            f'If you need to make any changes, please contact us:\n'
            f'Email : {settings.DEFAULT_FROM_EMAIL}\n'
            f'Phone : +234 706 367 0261\n\n'
            f'We look forward to welcoming you.\n\n'
            f'— T-Luxury Haven Hotel'
        ),
    )


def email_user_booking_cancelled(booking):
    """Email user when their booking is cancelled."""
    send_email(
        to_email = booking.user.email,
        subject  = 'Booking Cancelled — T-Luxury Haven Hotel',
        body     = (
            f'Dear {booking.user.first_name or booking.user.username},\n\n'
            f'Your booking #{booking.pk} for Room {booking.room.room_number} '
            f'({booking.check_in} to {booking.check_out}) has been cancelled.\n\n'
            f'If you believe this was a mistake or wish to rebook, '
            f'please contact us:\n'
            f'Email : {settings.DEFAULT_FROM_EMAIL}\n'
            f'Phone : +234 706 367 0261\n\n'
            f'We hope to welcome you in the future.\n\n'
            f'— T-Luxury Haven Hotel'
        ),
    )


def email_user_checkout_reminder(booking):
    """Email user the day their check-out date arrives."""
    send_email(
        to_email = booking.user.email,
        subject  = 'Check-out Today — T-Luxury Haven Hotel',
        body     = (
            f'Dear {booking.user.first_name or booking.user.username},\n\n'
            f'We hope you have had a wonderful stay at T-Luxury Haven Hotel.\n\n'
            f'This is a friendly reminder that your check-out is today:\n\n'
            f'--- CHECKOUT DETAILS ---\n'
            f'Room       : {booking.room.room_number} — {booking.room.room_type}\n'
            f'Check-out  : {booking.check_out} (by 12:00 PM)\n'
            f'Total Paid : ${booking.total_price}\n\n'
            f'Please ensure you settle any outstanding charges at the front desk.\n\n'
            f'Late checkout may be available on request — please ask our team.\n\n'
            f'Thank you for choosing T-Luxury Haven. We hope to see you again soon!\n\n'
            f'— T-Luxury Haven Hotel\n'
            f'tluxuryhaven@gmail.com | +234 706 367 0261'
        ),
    )