from django.db import models
from django.utils import timezone

class Ticket(models.Model):
    ticket_no = models.CharField(max_length=50)
    user_name = models.CharField(max_length=100)
    email = models.EmailField()
    dprt = models.CharField(max_length=100)  # Assuming 'dprt' means department
    post = models.CharField(max_length=100)
    env = models.CharField(max_length=50)
    pc_name = models.CharField(max_length=100)
    pc_ip = models.GenericIPAddressField()
    hw_sn = models.CharField(max_length=100)
    spa_no = models.CharField(max_length=50)
    report_type = models.CharField(max_length=100)
    hw_type = models.CharField(max_length=100)
    hw_type_encode = models.CharField(max_length=200)
    hw_model = models.CharField(max_length=100)
    apps_sw = models.CharField(max_length=200)
    report_desc = models.TextField()
    act_taken = models.TextField(null=True,blank=True)
    act_stat = models.CharField(max_length=50)
    date_created = models.DateField()
    time_created = models.TimeField()
    date_action = models.DateField(null=True, blank=True)
    time_action = models.TimeField(null=True, blank=True)
    taken_by = models.CharField(max_length=100)
    ftr_act = models.TextField(null=True, blank=True)
    fu_act = models.TextField(null=True, blank=True)

    


    def save(self, *args, **kwargs):
        # Automatically generate pc_name based on dprt, post, and env
        self.pc_name = f"{self.dprt}-{self.post}-{self.env}"

        # Set date_created and time_created to the current date and time if not set
        if not self.id:  # Only set on first save
            self.date_created = timezone.now().date()
            self.time_created = timezone.now().time()

        # Automatically generate the ticket number
        if not self.ticket_no:
            prefix = "AHBKPP"
            current_date = timezone.now()
            year = current_date.strftime('%y')
            month = current_date.strftime('%m')
            last_ticket = Ticket.objects.filter(ticket_no__startswith=prefix + year + month).order_by('ticket_no').last()
            if last_ticket:
                last_number = int(last_ticket.ticket_no[-3:])
                new_number = last_number + 1
            else:
                new_number = 1
            self.ticket_no = f"{prefix}{year}{month}{new_number:03d}"

        super(Ticket, self).save(*args, **kwargs)

    def __str__(self):
        return self.ticket_no

# models.py
# models.py

 # models.py

from django.contrib.auth.models import AbstractUser
from django.db import models

class CustomUser(AbstractUser):
    is_admin = models.BooleanField(default=False)
    is_technician = models.BooleanField(default=False)
    is_user = models.BooleanField(default=True)

  


