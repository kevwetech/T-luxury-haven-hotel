from django import forms
from .models import Booking, Room, GalleryImage, Testimonial


class BookingForm(forms.ModelForm):
    check_in  = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}))
    check_out = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}))

    class Meta:
        model   = Booking
        fields  = ['check_in', 'check_out', 'guests']



class RoomForm(forms.ModelForm):
    class Meta:
        model  = Room
        fields = ['room_number', 'room_type', 'description', 'price', 'capacity', 'image', 'is_active']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
        }



class GalleryImageForm(forms.ModelForm):
    class Meta:
        model  = GalleryImage
        fields = ['title', 'image', 'category', 'order', 'is_active']


class TestimonialForm(forms.ModelForm):
    class Meta:
        model  = Testimonial
        fields = ['name', 'location', 'quote', 'rating', 'photo', 'is_active']
        widgets = {
            'quote': forms.Textarea(attrs={'rows': 4}),
        }