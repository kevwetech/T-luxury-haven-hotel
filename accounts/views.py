from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.core.mail import send_mail
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib import messages
from django.contrib.auth.models import User
from .models import EmailVerificationToken
from django.template.loader import render_to_string
from .forms import CustomUserCreationForm




def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_active = False  # ← deactivate until email verified
            user.save()

            # Create verification token
            token_obj = EmailVerificationToken.objects.create(user=user)
            verify_url = request.build_absolute_uri(
                f'/accounts/verify-email/{token_obj.token}/'
            )

            # Send verification email
            send_mail(
                subject='Verify your email — T-Luxury Haven',
                message=f'Hi {user.username},\n\nClick the link below to verify your email:\n\n{verify_url}\n\nThis link is valid for 24 hours.\n\nT-Luxury Haven Team',
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                fail_silently=False,
            )

            messages.success(request, 'Account created! Please check your email to verify your account.')
            return redirect('login')
    else:
        form = CustomUserCreationForm()
    return render(request, 'accounts/register.html', {'form': form})


def verify_email(request, token):
    token_obj = get_object_or_404(EmailVerificationToken, token=token)
    user = token_obj.user

    if user.is_active:
        messages.info(request, 'Email already verified. Please log in.')
        return redirect('login')

    user.is_active = True
    user.save()
    token_obj.delete()  # token is single use

    login(request, user)
    messages.success(request, f'Email verified! Welcome, {user.username}!')
    return redirect('home')



def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect(request.GET.get('next', 'home'))
    else:
        form = AuthenticationForm()
    return render(request, 'accounts/login.html', {'form': form})


def logout_view(request):
    logout(request)
    return redirect('home')
