from django.contrib import admin
from .models import Room, RoomType, Booking, GalleryImage, Testimonial


@admin.register(RoomType)
class RoomTypeAdmin(admin.ModelAdmin):
    list_display = ['name']


@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = ['room_number', 'room_type', 'price', 'capacity', 'is_active']
    list_filter  = ['room_type', 'is_active']
    search_fields = ['room_number']


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display  = ['user', 'room', 'check_in', 'check_out', 'status', 'total_price']
    list_filter   = ['status']
    search_fields = ['user__username', 'room__room_number']


@admin.register(GalleryImage)
class GalleryImageAdmin(admin.ModelAdmin):
    list_display  = ['title', 'category', 'order', 'is_active']
    list_filter   = ['category', 'is_active']
    list_editable = ['order', 'is_active']


@admin.register(Testimonial)
class TestimonialAdmin(admin.ModelAdmin):
    list_display  = ['name', 'location', 'rating', 'is_active', 'created_at']
    list_filter   = ['rating', 'is_active']
    list_editable = ['is_active']

