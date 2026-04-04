from django.db import models
from django.contrib.auth.models import User
from django.db.models import Q
from django.core.exceptions import ValidationError


class RoomType(models.Model):
    name = models.CharField(max_length=100)  # e.g. Deluxe, Suite, Standard

    def __str__(self):
        return self.name


class Room(models.Model):
    room_number = models.CharField(max_length=10, unique=True)
    room_type   = models.ForeignKey(RoomType, on_delete=models.CASCADE)
    description = models.TextField(blank=True)
    price       = models.DecimalField(max_digits=8, decimal_places=2)
    capacity    = models.PositiveIntegerField(default=2)
    image       = models.ImageField(upload_to='rooms/', blank=True, null=True)
    is_active   = models.BooleanField(default=True)

    def __str__(self):
        return f"Room {self.room_number} — {self.room_type}"


class Booking(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('cancelled', 'Cancelled'),
    ]

    user        = models.ForeignKey(User, on_delete=models.CASCADE)
    room        = models.ForeignKey('Room', on_delete=models.CASCADE)
    check_in    = models.DateField()
    check_out   = models.DateField()
    guests      = models.PositiveIntegerField(default=1)
    status      = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    total_price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    created_at  = models.DateTimeField(auto_now_add=True)

    def __str__(self):  # ← also fix: was _str_, needs double underscores
        room_number = self.room.room_number if self.room_id else "No Room"
        return f"{self.user} — Room {room_number} ({self.check_in} to {self.check_out})"

    def clean(self):  # ← indented inside class
        if not self.room_id:
            return
        if self.check_in and self.check_out:
            if self.check_in >= self.check_out:
                raise ValidationError("Check-out date must be after check-in date.")
            if self.check_in < timezone.now().date():
                raise ValidationError("Check-in date cannot be in the past.")
            overlapping = Booking.objects.filter(
                room=self.room,
                status__in=['pending', 'confirmed'],
                check_in__lt=self.check_out,
                check_out__gt=self.check_in,
            )
            if self.pk:
                overlapping = overlapping.exclude(pk=self.pk)
            if overlapping.exists():
                raise ValidationError("This room is already booked for the selected dates.")

    def save(self, *args, **kwargs):  # ← indented inside class
        if self.check_in and self.check_out and self.room_id:
            nights = (self.check_out - self.check_in).days
            self.total_price = nights * self.room.price
        super().save(*args, **kwargs)

    class Meta:  # ← indented inside class
        ordering = ['-created_at']

        

class GalleryImage(models.Model):
    CATEGORY_CHOICES = [
        ('rooms',      'Rooms'),
        ('restaurants',     'Restaurants'),
        ('rooftopbar', 'Rooftopbar'),
        ('receptionist',  'Receptionist'),
        ('stairs',     'Stairs'),
        ('hallway',    'Hallway'),
    ]

    title    = models.CharField(max_length=100, blank=True)
    image    = models.ImageField(upload_to='gallery/')
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, default='rooms')
    order    = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['order', '-id']

    def __str__(self):
        return self.title or f"Gallery Image {self.id}"


class Testimonial(models.Model):
    name       = models.CharField(max_length=100)
    location   = models.CharField(max_length=100, blank=True)
    quote      = models.TextField()
    rating     = models.PositiveIntegerField(default=5)
    photo      = models.ImageField(upload_to='testimonials/', blank=True, null=True)
    is_active  = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} — {self.location}"
