from django.core.management.base import BaseCommand
import os
import django
import csv

from app1.models import Ticket

# Manually configure Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'trial.settings')  # Replace 'project_name' with your project name
django.setup()

class Command(BaseCommand):
    help = 'Load data from CSV file into the Ticket model'

    def handle(self, *args, **kwargs):
        with open('C:/Users/Administrator/Downloads/Trial/tickets.csv', 'r') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                ticket, created = Ticket.objects.get_or_create(
                    ticket_no=row['ticket_no'],
                    user_name=row['user_name'],
                    email=row['email'],
                    dprt=row['dprt'],
                    post=row['post'],
                    env=row['env'],
                    pc_name=row['pc_name'],
                    pc_ip=row['pc_ip'],
                    hw_sn=row['hw_sn'],
                    spa_no=row['spa_no'],
                    report_type=row['report_type'],
                    hw_type=row['hw_type'],
                    hw_type_encode=row['hw_type_encode'],
                    hw_model=row['hw_model'],
                    apps_sw=row['apps_sw'],
                    report_desc=row['report_desc'],
                    act_taken=row['act_taken'],
                    act_stat=row['act_stat'],
                    date_created=row['date_created'],
                    time_created=row['time_created'],
                    date_action=row['date_action'],
                    time_action=row['time_action'],
                    taken_by=row['taken_by'],
                    ftr_act=row['ftr_act'],
                    fu_act=row['fu_act']
                )
                if created:
                    self.stdout.write(self.style.SUCCESS(f"Ticket {ticket.ticket_no} created"))
                else:
                    self.stdout.write(self.style.WARNING(f"Ticket {ticket.ticket_no} already exists"))
