import os
import sendgrid
from sendgrid.helpers.mail import Mail
from django.conf import settings
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from rooms.tokens import email_token


def send_email(to_email, subject, body):
    """Send email via SendGrid HTTP API."""
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


def send_verification_email(request, user):
    uid        = urlsafe_base64_encode(force_bytes(user.pk))
    token      = email_token.make_token(user)
    verify_url = request.build_absolute_uri(f'/accounts/verify/{uid}/{token}/')

    send_email(
        to_email = user.email,
        subject  = 'Verify your T-Luxury Haven account',
        body     = (
            f'Hi {user.username},\n\n'
            f'Welcome to T-Luxury Haven Hotel!\n\n'
            f'Click the link below to verify your email:\n\n'
            f'{verify_url}\n\n'
            f'This link expires in 24 hours.\n\n'
            f'If you did not create this account, ignore this email.\n\n'
            f'— T-Luxury Haven Hotel'
        ),
    )


def send_password_reset_email(request, user):
    from django.contrib.auth.tokens import default_token_generator as reset_token
    uid       = urlsafe_base64_encode(force_bytes(user.pk))
    token     = reset_token.make_token(user)
    reset_url = request.build_absolute_uri(f'/accounts/reset-password/{uid}/{token}/')

    send_email(
        to_email = user.email,
        subject  = 'Reset your T-Luxury Haven password',
        body     = (
            f'Hi {user.username},\n\n'
            f'You requested a password reset.\n\n'
            f'Click the link below to reset your password:\n\n'
            f'{reset_url}\n\n'
            f'This link expires in 1 hour.\n\n'
            f'If you did not request this, ignore this email.\n\n'
            f'— T-Luxury Haven Hotel'
        ),
    )


def send_password_changed_email(user):
    send_email(
        to_email = user.email,
        subject  = 'Your T-Luxury Haven password was changed',
        body     = (
            f'Hi {user.username},\n\n'
            f'Your password was recently changed.\n\n'
            f'If you did not do this, contact us immediately at {settings.DEFAULT_FROM_EMAIL}.\n\n'
            f'— T-Luxury Haven Hotel'
        ),
    )
