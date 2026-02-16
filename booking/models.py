from django.db import models
from django.utils import timezone

class Room(models.Model):
    ROOM_TYPES = (
        ('standard', 'Standard'),
        ('premium', 'Premium'),
        ('suite', 'Suite'),
    )
    title = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    description = models.TextField()
    price = models.DecimalField(max_digits=8, decimal_places=2)
    image = models.ImageField(upload_to='rooms/')
    room_type = models.CharField(max_length=20, choices=ROOM_TYPES, default='standard')

    def __str__(self):
        return self.title

class Booking(models.Model):
    room = models.ForeignKey(Room, on_delete=models.CASCADE)
    check_in_date = models.DateField()
    check_in_time = models.TimeField()
    check_out_date = models.DateField()
    check_out_time = models.TimeField()
    adults = models.PositiveIntegerField(default=1)
    children = models.PositiveIntegerField(default=0)
    rooms_count = models.PositiveIntegerField(default=1)
    no_of_days = models.PositiveIntegerField(default=1)

    subtotal = models.DecimalField(max_digits=10, decimal_places=2)
    tax = models.DecimalField(max_digits=10, decimal_places=2)
    total = models.DecimalField(max_digits=10, decimal_places=2)

    # Billing info
    name = models.CharField(max_length=200)
    email = models.EmailField()
    phone = models.CharField(max_length=20)
    address = models.CharField(max_length=255)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    special_requests = models.TextField(blank=True, null=True)


    booked_at = models.DateTimeField(default=timezone.now)
    payment_status = models.CharField(max_length=20, default='pending')



    def __str__(self):
        return f"{self.name} - {self.room.title} ({self.check_in_date} to {self.check_out_date})"
