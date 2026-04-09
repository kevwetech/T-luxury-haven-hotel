from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, update_session_auth_hash
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.mail import send_mail
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.conf import settings
from django.db.models import Sum
from rooms.tokens import email_token
from accounts.forms import CustomUserCreationForm
from rooms.models import Booking

# We reuse Django's PasswordResetTokenGenerator for password reset
from django.contrib.auth.tokens import default_token_generator as reset_token


# ── HELPERS ──────────────────────────────────────────────

def send_verification_email(request, user):
    uid        = urlsafe_base64_encode(force_bytes(user.pk))
    token      = email_token.make_token(user)
    verify_url = request.build_absolute_uri(f'/accounts/verify/{uid}/{token}/')
    send_mail(
        subject='Verify your T-Luxury Haven account',
        message=(
            f'Hi {user.username},\n\n'
            f'Welcome to T-Luxury Haven Hotel!\n\n'
            f'Click the link below to verify your email:\n\n'
            f'{verify_url}\n\n'
            f'This link expires in 24 hours.\n\n'
            f'If you did not create this account, ignore this email.\n\n'
            f'— T-Luxury Haven Hotel'
        ),
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        fail_silently=False,
    )


# ── REGISTER ─────────────────────────────────────────────

def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user           = form.save(commit=False)
            user.email     = form.cleaned_data['email']
            user.is_active = False
            user.save()
            request.session['pending_username'] = user.username
            try:
                send_verification_email(request, user)
                messages.success(request, 'Account created! Please check your email to verify.')
            except Exception:
                messages.warning(request, 'Account created but verification email failed. Contact support.')
            return redirect('verify_email_notice')
    else:
        form = CustomUserCreationForm()
    return render(request, 'accounts/register.html', {'form': form})


# ── VERIFY EMAIL ──────────────────────────────────────────

def verify_email_notice(request):
    username = request.session.get('pending_username', '')
    return render(request, 'accounts/verify_email.html', {'username': username})


def verify_email(request, uidb64, token):
    try:
        uid  = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if user and email_token.check_token(user, token):
        user.is_active = True
        user.save()
        login(request, user)
        messages.success(request, f'Welcome, {user.username}! Your email has been verified.')
        return redirect('home')
    else:
        messages.error(request, 'Verification link is invalid or expired.')
        return redirect('verify_email_notice')


def resend_verification(request):
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        try:
            user = User.objects.get(username=username, is_active=False)
            send_verification_email(request, user)
            messages.success(request, 'Verification email resent! Check your inbox.')
        except User.DoesNotExist:
            messages.error(request, 'No unverified account found.')
        except Exception:
            messages.error(request, 'Could not send email. Try again later.')
    return redirect('verify_email_notice')


# ── LOGIN / LOGOUT ────────────────────────────────────────

def login_view(request):
    if request.method == 'POST':
        form        = AuthenticationForm(data=request.POST)
        remember_me = request.POST.get('remember_me')

        if form.is_valid():
            user = form.get_user()
            if not user.is_active:
                messages.error(request, 'Please verify your email before logging in.')
                return redirect('verify_email_notice')

            login(request, user)

            # Remember me — extend session to 2 weeks, else expire on browser close
            if remember_me:
                request.session.set_expiry(60 * 60 * 24 * 14)  # 14 days
            else:
                request.session.set_expiry(0)  # expires when browser closes

            return redirect(request.GET.get('next', 'home'))
        else:
            messages.error(request, 'Invalid username or password.')
    else:
        form = AuthenticationForm()
    return render(request, 'accounts/login.html', {'form': form})


def logout_view(request):
    logout(request)
    messages.success(request, 'You have been logged out.')
    return redirect('home')


# ── FORGOT PASSWORD ───────────────────────────────────────

def forgot_password(request):
    sent = False
    if request.method == 'POST':
        email = request.POST.get('email', '').strip()
        # Always show success to avoid user enumeration
        sent = True
        try:
            user = User.objects.get(email=email, is_active=True)
            uid   = urlsafe_base64_encode(force_bytes(user.pk))
            token = reset_token.make_token(user)
            reset_url = request.build_absolute_uri(
                f'/accounts/reset-password/{uid}/{token}/'
            )
            send_mail(
                subject='Reset your T-Luxury Haven password',
                message=(
                    f'Hi {user.username},\n\n'
                    f'You requested a password reset for your T-Luxury Haven account.\n\n'
                    f'Click the link below to reset your password:\n\n'
                    f'{reset_url}\n\n'
                    f'This link expires in 1 hour.\n\n'
                    f'If you did not request this, ignore this email — your password will not change.\n\n'
                    f'— T-Luxury Haven Hotel'
                ),
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[email],
                fail_silently=True,
            )
        except User.DoesNotExist:
            pass  # Don't reveal if email exists

    return render(request, 'accounts/forgot_password.html', {'sent': sent})


# ── RESET PASSWORD ────────────────────────────────────────

def reset_password(request, uidb64, token):
    # Validate the token first
    try:
        uid  = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    token_valid = user is not None and reset_token.check_token(user, token)

    if not token_valid:
        return render(request, 'accounts/reset_password.html', {'invalid': True})

    success = False
    errors  = {}

    if request.method == 'POST':
        new1 = request.POST.get('new_password1', '')
        new2 = request.POST.get('new_password2', '')

        if len(new1) < 8:
            errors['new_password1'] = ['Password must be at least 8 characters.']
        if new1 != new2:
            errors['new_password2'] = ['Passwords do not match.']

        if not errors:
            user.set_password(new1)
            user.save()
            success = True

            # Notify user by email
            send_mail(
                subject='Your T-Luxury Haven password was reset',
                message=(
                    f'Hi {user.username},\n\n'
                    f'Your password was successfully reset.\n\n'
                    f'If you did not do this, contact us immediately at {settings.DEFAULT_FROM_EMAIL}.\n\n'
                    f'— T-Luxury Haven Hotel'
                ),
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                fail_silently=True,
            )

    return render(request, 'accounts/reset_password.html', {
        'uidb64':  uidb64,
        'token':   token,
        'success': success,
        'errors':  errors,
        'invalid': False,
    })


# ── PROFILE ───────────────────────────────────────────────

@login_required
def profile(request):
    if request.method == 'POST':
        user            = request.user
        user.first_name = request.POST.get('first_name', '').strip()
        user.last_name  = request.POST.get('last_name', '').strip()
        user.email      = request.POST.get('email', '').strip()
        user.save()
        messages.success(request, 'Profile updated successfully.')
        return redirect('profile')

    bookings           = Booking.objects.filter(user=request.user).order_by('-created_at')
    total_bookings     = bookings.count()
    confirmed_bookings = bookings.filter(status='confirmed').count()
    total_spent        = bookings.filter(status='confirmed').aggregate(
                           total=Sum('total_price'))['total'] or 0
    recent_bookings    = bookings[:5]

    return render(request, 'accounts/profile.html', {
        'total_bookings':     total_bookings,
        'confirmed_bookings': confirmed_bookings,
        'total_spent':        total_spent,
        'recent_bookings':    recent_bookings,
    })


# ── CHANGE PASSWORD ───────────────────────────────────────

@login_required
def change_password(request):
    success = False
    errors  = {}

    if request.method == 'POST':
        current = request.POST.get('current_password', '')
        new1    = request.POST.get('new_password1', '')
        new2    = request.POST.get('new_password2', '')

        if not request.user.check_password(current):
            errors['current_password'] = ['Current password is incorrect.']
        if len(new1) < 8:
            errors['new_password1'] = ['Password must be at least 8 characters.']
        if new1 != new2:
            errors['new_password2'] = ['Passwords do not match.']

        if not errors:
            request.user.set_password(new1)
            request.user.save()
            update_session_auth_hash(request, request.user)
            success = True
            send_mail(
                subject='Your T-Luxury Haven password was changed',
                message=(
                    f'Hi {request.user.username},\n\n'
                    f'Your password was recently changed.\n\n'
                    f'If you did not do this, contact us at {settings.DEFAULT_FROM_EMAIL}.\n\n'
                    f'— T-Luxury Haven Hotel'
                ),
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[request.user.email],
                fail_silently=True,
            )
        else:
            messages.error(request, 'Please fix the errors below.')

    class FakeForm:
        def __init__(self, errs): self.errors = errs

    return render(request, 'accounts/change_password.html', {
        'form':    FakeForm(errors),
        'success': success,
    })