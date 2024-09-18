from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import get_user_model
from django.urls import reverse_lazy
from django.views import generic
from .forms import ChatbotForm, CustomUserCreationForm
from .models import Ticket
import time
import openai
# from openai.error import RateLimitError
from .chatbot import recommend_action, update_model_with_new_data

# Set your OpenAI API key here
openai.api_key = "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"

# Ensure correct imports
from .chatbot import recommend_action, update_model_with_new_data

User = get_user_model()

# Landing Page View
def landing_page(request):
    return render(request, 'landing_page.html')

# Chatbot View
@login_required
def chatbot_view(request):
    # Initialize the form with the logged-in user
    form = ChatbotForm(user=request.user)
    action = None  # Placeholder for recommended action
    chatgpt_response = None  # Placeholder for ChatGPT response

    if request.method == 'POST':
        # Handle form re-submission with POST data
        form = ChatbotForm(request.POST, user=request.user)

        if form.is_valid():
            # Extract cleaned form data
            hw_type = form.cleaned_data['hw_type']
            apps_sw = form.cleaned_data['apps_sw']
            report_type = form.cleaned_data['report_type']
            report_desc = form.cleaned_data['report_desc']
            pc_ip = form.cleaned_data['pc_ip']
            dprt = form.cleaned_data['dprt']
            post = form.cleaned_data['post']
            env = form.cleaned_data['env']
            action = form.cleaned_data.get('action', None)  # Handle empty action case

            if 'resolved' in request.POST:
                # User is responding to chatbot recommendation (feedback form)
                resolved = request.POST.get('resolved')
                act_stat = 'S' if resolved == 'yes' else 'O'

                # Save feedback to the Ticket model
                Ticket.objects.create(
                    hw_type=hw_type,
                    apps_sw=apps_sw,
                    report_type=report_type,
                    report_desc=report_desc,
                    pc_ip=pc_ip,
                    act_taken=action,
                    act_stat=act_stat,
                    user_name=request.user.username,
                    email=request.user.email,
                    dprt=dprt,
                    post=post,
                    env=env,
                    taken_by='chatbot'
                )

                # Update model with new data if necessary
                update_model_with_new_data(hw_type, apps_sw, report_type, report_desc, action)

                return redirect('user_tickets.html')  # Redirect to the chatbot view after saving

            else:
                # Handle initial form submission
                # Step 1: Try to get a recommendation from your internal model
                action = recommend_action(hw_type, apps_sw, report_type, report_desc)
                resolved = request.POST.get('resolved')
                act_stat = 'S' if resolved == 'yes' else 'O'
            
                # Step 2: Fallback to ChatGPT if no recommendation is found
                if not action:
                    action = get_chatgpt_recommendation(hw_type, apps_sw, report_type, report_desc)
                # Save feedback to the Ticket model
                Ticket.objects.create(
                    hw_type=hw_type,
                    apps_sw=apps_sw,
                    report_type=report_type,
                    report_desc=report_desc,
                    pc_ip=pc_ip,
                    act_taken=action,
                    act_stat=act_stat,  
                    user_name=request.user.username,
                    email=request.user.email,
                    dprt=dprt,
                    post=post,
                    env=env,    
                    taken_by='chatbot'
                )
                # Render the response page with the recommended action
                return render(request, 'chatbot_response.html', {
                    'hw_type': hw_type,
                    'apps_sw': apps_sw,
                    'pc_ip': pc_ip,
                    'report_type': report_type,
                    'report_desc': report_desc,
                    'action': action,
                    'form': form,
                })
                return redirect('user_tickets.html')

    # Render the form initially or if invalid
    return render(request, 'chatbot_form.html', {'form': form})


def get_chatgpt_recommendation(hw_type, apps_sw, report_type, report_desc):
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            # model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": f"Hardware Type: {hw_type}\nSoftware: {apps_sw}\nReport Type: {report_type}\nDescription: {report_desc}"}
            ],
            temperature=1.0,
            max_tokens=256,
            top_p=1,
            frequency_penalty=0,
            presence_penalty=0,
        )

        action = response['choices'][0]['message']['content'].strip()
        return action

    except openai.error.RateLimitError:
        return "We're experiencing high traffic. Please try again later."


# Signup View
class SignUp(generic.CreateView):
    form_class = CustomUserCreationForm
    success_url = reverse_lazy('login')
    template_name = 'signup.html'

    def form_valid(self, form):
        user = form.save(commit=False)
        user.is_admin = form.cleaned_data.get('is_admin')
        user.is_technician = form.cleaned_data.get('is_technician')
        user.is_user = form.cleaned_data.get('is_user')
        user.save()
        return super().form_valid(form)

# Login View
def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')

            user = authenticate(request, username=username, password=password)

            if user is not None:
                login(request, user)
                if user.is_admin:
                    return redirect('admin_dashboard')
                elif user.is_technician:
                    return redirect('technician_dashboard')
                elif user.is_user:
                    return redirect('user_dashboard')
                else:
                    return redirect('login')
    else:
        form = AuthenticationForm()
    return render(request, 'login.html', {'form': form})

# Logout View
@login_required
def logout_view(request):
    logout(request)
    return redirect('login')

# Admin Dashboard View
@login_required
def admin_dashboard(request):
    if request.user.is_admin:
        # Get the filters from the GET parameters
        report_type = request.GET.get('report_type', '')
        act_stat = request.GET.get('act_stat', '')
        taken_by = request.GET.get('taken_by', '')

        # Start with all tickets
        tickets = Ticket.objects.all()

        # Apply filters if they are present
        if report_type:
            tickets = tickets.filter(report_type=report_type)
        if act_stat:
            tickets = tickets.filter(act_stat=act_stat)
        if taken_by:
            tickets = tickets.filter(taken_by__icontains=taken_by)

        # Handle sorting
        sort_by = request.GET.get('sort_by', 'date_created')  # Default sort by date_created
        sort_order = request.GET.get('sort_order', 'asc')
        if sort_order == 'desc':
            sort_by = '-' + sort_by

        tickets = tickets.order_by(sort_by)

        # Pass the filters back to the template
        context = {
            'tickets': tickets,
            'report_type': report_type,
            'act_stat': act_stat,
            'taken_by': taken_by,
            'sort_by': request.GET.get('sort_by', 'date_created'),
            'sort_order': request.GET.get('sort_order', 'asc')
        }
        
        return render(request, 'admin_dashboard.html', context)

    return redirect('login')

# Technician Dashboard View
@login_required
def technician_dashboard(request):
    if request.user.is_technician:
        return render(request, 'technician_dashboard.html')
    return redirect('login')

from django.db.models import Q
@login_required
def open_tickets(request):
    if request.user.is_technician:
        tickets = Ticket.objects.filter(Q(act_stat='O') | Q(act_stat='DT')).order_by('-date_created')
        return render(request, 'open_tickets.html', {'tickets': tickets})
    return redirect('login')

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from .models import Ticket
from django.utils import timezone

@login_required
def update_ticket(request, ticket_id):
    ticket = get_object_or_404(Ticket, id=ticket_id)

    if request.method == 'POST':
        action_taken = request.POST.get('action_taken', '').strip()
        act_stat = request.POST.get('act_stat', '').strip()
        ftr_act = request.POST.get('ftr_act', '').strip()
        fu_act = request.POST.get('fu_act', '').strip()

        # Check if any action is taken and status is provided
        if action_taken:
            ticket.act_taken = action_taken
            ticket.act_stat = act_stat
            ticket.taken_by = request.user.username

            # Always capture the date_action and time_action whenever an update is made
            current_time = timezone.now()
            ticket.date_action = current_time.date()  # Save current date
            ticket.time_action = current_time.time()  # Save current time

        # Save future action (ftr_act) if provided
        if ftr_act in ['C', 'RTV', 'P', 'AN']:
            ticket.ftr_act = ftr_act

        # Save follow-up action (fu_act) if provided
        if fu_act:
            ticket.fu_act = fu_act

        ticket.save()  # Save all updates to the ticket
        return redirect('open_tickets')

    return render(request, 'update_ticket.html', {'ticket': ticket})


@login_required
def closed_tickets(request):
    if request.user.is_technician:
        tickets = Ticket.objects.filter(act_stat='S', taken_by=request.user.username).order_by('-date_action')
        return render(request, 'closed_tickets.html', {'tickets': tickets})
    return redirect('login')

# User Dashboard View
@login_required
def user_dashboard(request):
    if request.user.is_user:
        return render(request, 'user_dashboard.html')
    return redirect('login')

@login_required
def user_tickets(request):
    if request.user.is_user:
        tickets = Ticket.objects.filter(user_name=request.user.username, email=request.user.email)
        return render(request, 'user_tickets.html', {'tickets': tickets})
    return redirect('login')

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from app1.models import Ticket

@login_required
def dashboard_analysis(request):
    if request.user.is_admin:  # Ensure that only admin users can access the page
        total_tickets = Ticket.objects.count()  # Count total tickets
        return render(request, 'dashboard_analysis.html', {'total_tickets': total_tickets})
    return redirect('login')  # Redirect non-admin users to the login page


import pygwalker as pyg
import pandas as pd
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from app1.models import Ticket


@login_required
def dashboard_analysis(request):
    if request.user.is_admin:  # Ensure only admin users can access the page
        total_tickets = Ticket.objects.count()  # Count total tickets

        # Convert Django queryset to DataFrame
        tickets_df = pd.DataFrame(list(Ticket.objects.all().values()))

        # Use Pygwalker to create an interactive chart
        pyg_html = pyg.walk(tickets_df).to_html()  # Generate Pygwalker HTML code

        return render(request, 'dashboard_analysis.html', {
            'total_tickets': total_tickets,
            'pyg_html': pyg_html  # Pass Pygwalker HTML to template
        })

    return redirect('login')  # Redirect non-admin users to login
