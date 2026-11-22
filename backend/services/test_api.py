import pytest
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
from rest_framework.test import APIClient
from datetime import date, time
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
    
    
@pytest.mark.django_db
def test_multitenancy():
    owner_1 = User.objects.create_user(username="First_owner", password="testpass")
    owner_2 = User.objects.create_user(username="Second_owner", password="testpass")
    
    owner_1.profile.role = "owner"
    owner_1.profile.save()
    
    owner_2.profile.role = "owner"
    owner_2.profile.save()
    
    auto_1 = Autoservice.objects.create(name="Test_Service_1",
                                        owner=owner_1,
                                        address="Test Address",
                                        phone='12345678')
    
    auto_2 = Autoservice.objects.create(name="Test_Service_2",
                                        owner=owner_2,
                                        address="Test Address",
                                        phone="12345678")
    
    service_1 = Service.objects.create(autoservice=auto_1,
                                       name="Test_owner 1",
                                       price=67.00,
                                       duration_min=90)
    
    service_2 = Service.objects.create(autoservice=auto_2,
                                       name="Test_owner 2",
                                       price=100.00,
                                       duration_min=60)
    
    client = APIClient()
    client.force_authenticate(user=owner_2)
    response = client.get('/api/services/')
    
    assert response.status_code == 200
    assert len(response.data['results']) == 1
    

@pytest.mark.django_db
def test_race_condition():
    user = User.objects.create_user(username="test_user_1", password="testpass")
    
    auto = Autoservice.objects.create(name="Test_Service_1",
                                        owner=user,
                                        address="Test Address",
                                        phone='12345678')
    
    master = Master.objects.create(autoservice = auto,
                                    first_name = 'Test',
                                    last_name = 'Master',
                                    email = 'master@test.com',
                                    specialization = 'test')
    
    service = Service.objects.create(autoservice=auto,
                                       name="Test_owner 1",
                                       price=67.00,
                                       duration_min=90)
    
    booking = Booking.objects.create(autoservice=auto,
                                       client=user,
                                       service=service,
                                       master=master,
                                       date=date(2026, 11, 23),
                                       start_time=time(19, 30),
                                       end_time=time(20, 00),
                                       price=90.00,
                                       status="pending")
    
    
    client = APIClient()
    client.force_authenticate(user=user)
    
    data = {
        "service": service.id,
        "master": master.id,
        "date": "2026-11-23",
        "start_time": "19:45:00",
        "end_time": "20:15:00",
        "status": "pending"
    }
    
    response = client.post("/api/bookings/", data)
    
    
    assert response.status_code == 400
    assert "already booked" in str(response.data)
    
    