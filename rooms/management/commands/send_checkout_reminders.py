"""
Management command to send checkout reminder emails.

Run daily via cron or Railway cron job:
  python manage.py send_checkout_reminders

Add to Railway / cron:
  0 7 * * * python manage.py send_checkout_reminders
  (Runs every day at 7:00 AM)
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from rooms.models import Booking
from rooms.emails import email_user_checkout_reminder


class Command(BaseCommand):
    help = 'Send checkout reminder emails to guests checking out today.'

    def handle(self, *args, **options):
        today = timezone.now().date()

        checkouts = Booking.objects.filter(
            check_out=today,
            status='confirmed',
        ).select_related('user', 'room')

        if not checkouts.exists():
            self.stdout.write(self.style.WARNING(f'No checkouts today ({today}).'))
            return

        sent  = 0
        failed = 0

        for booking in checkouts:
            try:
                email_user_checkout_reminder(booking)
                sent += 1
                self.stdout.write(
                    self.style.SUCCESS(
                        f'✓ Sent to {booking.user.email} — Booking #{booking.pk}'
                    )
                )
            except Exception as e:
                failed += 1
                self.stdout.write(
                    self.style.ERROR(
                        f'✗ Failed for Booking #{booking.pk}: {e}'
                    )
                )

        self.stdout.write(
            self.style.SUCCESS(
                f'\nDone. {sent} sent, {failed} failed. Date: {today}'
            )
        )