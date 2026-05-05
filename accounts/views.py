from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, update_session_auth_hash
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.conf import settings
from django.db.models import Sum
from rooms.tokens import email_token
from accounts.forms import CustomUserCreationForm, EmailAuthenticationForm
from rooms.models import Booking
from accounts.email_utils import (
    send_email,
    send_verification_email,
    send_password_reset_email,
    send_password_changed_email,
)

# Django's built-in token generator for password reset
from django.contrib.auth.tokens import default_token_generator as reset_token


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
            except Exception as e:
                messages.warning(request, f'Account created but verification email failed: {e}')
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
        except Exception as e:
            messages.error(request, f'Could not send email: {e}')
    return redirect('verify_email_notice')


# ── LOGIN / LOGOUT ────────────────────────────────────────


def login_view(request):
    if request.method == 'POST':
        form        = EmailAuthenticationForm(data=request.POST)
        remember_me = request.POST.get('remember_me')
        
        if form.is_valid():
            
            user = form.get_user()
            login(request, user)
            
            if remember_me:
                request.session.set_expiry(60 * 60 * 24 * 14)  # 14 days
                
            else:
                request.session.set_expiry(0)  # expires on browser close
            return redirect(request.GET.get('next', 'home'))
            
        else:
            messages.error(request, 'Invalid email or password.')
            
    else:
        form = EmailAuthenticationForm()
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
        sent  = True  # always show success to prevent email enumeration
        try:
            user = User.objects.get(email=email, is_active=True)
            send_password_reset_email(request, user)
        except User.DoesNotExist:
            pass  # don't reveal if email exists
        except Exception as e:
            print(f'Password reset email error: {e}')

    return render(request, 'accounts/forgot_password.html', {'sent': sent})


# ── RESET PASSWORD ────────────────────────────────────────

def reset_password(request, uidb64, token):
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
            try:
                send_email(
                    to_email = user.email,
                    subject  = 'Your T-Luxury Haven password was reset',
                    body     = (
                        f'Hi {user.username},\n\n'
                        f'Your password was successfully reset.\n\n'
                        f'If you did not do this, contact us immediately at '
                        f'{settings.DEFAULT_FROM_EMAIL}.\n\n'
                        f'— T-Luxury Haven Hotel'
                    ),
                )
            except Exception:
                pass

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
            try:
                send_password_changed_email(request.user)
            except Exception:
                pass
        else:
            messages.error(request, 'Please fix the errors below.')

    class FakeForm:
        def __init__(self, errs): self.errors = errs

    return render(request, 'accounts/change_password.html', {
        'form':    FakeForm(errors),
        'success': success,
    })