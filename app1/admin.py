from django.contrib import admin

# Register your models here.
from .models import Ticket,CustomUser
admin.site.register(Ticket)
admin.site.register(CustomUser)