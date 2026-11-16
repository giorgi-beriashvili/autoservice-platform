import pytest
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
from users.models import Autoservice, Profile
from services.models import Service, Master, Booking

@pytest.mark.django_db

def test_can_cancel_false_less_than_2_hours():
    client_user = User.objects.create_user(username="test_client", password='testpass')
    owner_user = User.objects.create_user(username="test_owner", password="testpass")
    
    client_user.profile.role = "client"
    client_user.profile.save()

    owner_user.profile.role = "owner"
    owner_user.profile.save()
    
    autoservice = Autoservice.objects.create(name = 'Test Service',
                                             owner = owner_user,
                                             address = 'Test Address',
                                             phone = '12345678')
    
    service = Service.objects.create(autoservice = autoservice,
                                     name = 'Test Service',
                                     price = 123.00,
                                     duration_min = 30)
     
    master = Master.objects.create(autoservice = autoservice,
                                    first_name = 'Test',
                                    last_name = 'Master',
                                    email = 'master@test.com',
                                    specialization = 'test')
    
    
    now = timezone.now()
    booking_date = now.date()
    start_time = (now + timedelta(hours=1)).time()
    end_time = (now + timedelta(hours=1, minutes=30)).time()
    
    booking = Booking.objects.create(autoservice=autoservice,
                                     client=client_user,
                                     service=service,
                                     master=master,
                                     date=booking_date,
                                     start_time=start_time,
                                     end_time=end_time,
                                     status='pending')
    
    assert booking.can_cancel() is False
    