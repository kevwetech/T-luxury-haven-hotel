from django.urls import path
from . import views

urlpatterns = [
    path('', views.home,           name='home'),
    path('room/<int:pk>/', views.room_detail,    name='room_detail'),
    path('room/<int:pk>/book/', views.book_room,      name='book_room'),
    path('my-bookings/', views.my_bookings,    name='my_bookings'),
    path('cancel/<int:pk>/', views.cancel_booking, name='cancel_booking'),
    path('rooms/', views.rooms_page, name='rooms'),
    path('about/',   views.about,   name='about'),
    path('gallery/', views.gallery, name='gallery'),
    path('contact/', views.contact, name='contact'),
    path('booking/paystack/callback/', views.paystack_callback, name='paystack_callback'),
    # Dashboard
    path('dashboard/',                          views.dashboard,                name='dashboard'),
    path('dashboard/bookings/',                 views.dashboard_bookings,       name='dashboard_bookings'),
    path('dashboard/bookings/<int:pk>/update/', views.dashboard_booking_update, name='dashboard_booking_update'),
    path('dashboard/rooms/',                    views.dashboard_rooms,          name='dashboard_rooms'),
    path('dashboard/rooms/add/',                views.dashboard_room_add,       name='dashboard_room_add'),
    path('dashboard/rooms/<int:pk>/edit/',      views.dashboard_room_edit,      name='dashboard_room_edit'),
    path('dashboard/rooms/<int:pk>/delete/',    views.dashboard_room_delete,    name='dashboard_room_delete'),
    # Gallery dashboard
    path('dashboard/gallery/',                views.dashboard_gallery,           name='dashboard_gallery'),
    path('dashboard/gallery/add/',            views.dashboard_gallery_add,       name='dashboard_gallery_add'),
    path('dashboard/gallery/<int:pk>/delete/', views.dashboard_gallery_delete,   name='dashboard_gallery_delete'),

    # Testimonials dashboard
    path('dashboard/testimonials/',                    views.dashboard_testimonials,        name='dashboard_testimonials'),
    path('dashboard/testimonials/add/',                views.dashboard_testimonial_add,     name='dashboard_testimonial_add'),
    path('dashboard/testimonials/<int:pk>/edit/',      views.dashboard_testimonial_edit,    name='dashboard_testimonial_edit'),
    path('dashboard/testimonials/<int:pk>/delete/',    views.dashboard_testimonial_delete,  name='dashboard_testimonial_delete'),
]