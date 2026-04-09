from django.urls import path
from . import views

urlpatterns = [
    path('register/',                        views.register,            name='register'),
    path('login/',                           views.login_view,          name='login'),
    path('logout/',                          views.logout_view,         name='logout'),
    path('profile/',                         views.profile,             name='profile'),
    path('change-password/',                 views.change_password,     name='change_password'),
    path('verify/',                          views.verify_email_notice, name='verify_email_notice'),
    path('verify/<uidb64>/<token>/',         views.verify_email,        name='verify_email'),
    path('resend-verification/',             views.resend_verification,  name='resend_verification'),
    path('forgot-password/',                 views.forgot_password,     name='forgot_password'),
    path('reset-password/<uidb64>/<token>/', views.reset_password,      name='reset_password'),
]