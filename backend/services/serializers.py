from rest_framework import serializers
from .models import Service, Master, Booking
from datetime import datetime, timedelta
from django.utils import timezone


class ServiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Service
        fields = ['id', 'name', 'description', 'price', 'duration_min', 'is_active']


class MasterSerializer(serializers.ModelSerializer):
    class Meta:
        model = Master
        fields = ['id', 'first_name', 'last_name', 'phone', 'email', 'bio', 'specialization', 'services', 'is_active']
        

class BookingSerializer(serializers.ModelSerializer):
    
    can_cancel = serializers.ReadOnlyField()
    
    class Meta:
        model = Booking
        fields = ['id', 'client', 'service', 'master', 'date', 'start_time', 'price', 'status', 'can_cancel']
        read_only_fields = ['price', 'client', 'end_time']
        
    # Prevent double-booking: check if this time slot is already taken(race condition) 
    def validate(self, attrs):
        master = attrs["master"]
        service = attrs["service"]
        date = attrs["date"]
        start_time = attrs["start_time"]
        
        calculated_end = (datetime.combine(date, start_time) + timedelta(minutes=service.duration_min)).time()

        conflicts = Booking.objects.filter(master=master, date=date, start_time__lt=calculated_end, end_time__gt=start_time)
        booking_datetime = datetime.combine(date, start_time)
        booking_datetime = timezone.make_aware(booking_datetime) # converts from naive to UTC
        
        if booking_datetime < timezone.now():
            raise serializers.ValidationError("Cannot book in the past.")
        
        if conflicts.exists():
            raise serializers.ValidationError("This time slot is already booked.")
        
        return attrs
    
