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
    form = ChatbotForm()
    action = None  # To hold the recommended action
    chatgpt_response = None  # To hold the ChatGPT response

    if request.method == 'POST':
        if 'action' in request.POST:
            # User is responding to chatbot recommendation
            resolved = request.POST.get('resolved', None)
            hw_type = request.POST.get('hw_type')
            apps_sw = request.POST.get('apps_sw')
            report_type = request.POST.get('report_type')
            report_desc = request.POST.get('report_desc')
            pc_ip = request.POST.get('pc_ip')
            action = request.POST.get('action')

            if resolved:
                act_stat = 'S' if resolved == 'yes' else 'O'
                # Save the Ticket model with the user's response
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
                    taken_by='chatbot'
                )

                # Update model with new data
                update_model_with_new_data(hw_type, apps_sw, report_type, report_desc, action)

            return redirect('chatbot_view')

        elif 'generate_new_action' in request.POST:
            # Handle the "Generate New Action" button click
            report_desc = request.POST.get('report_desc')
            hw_type = request.POST.get('hw_type')
            apps_sw = request.POST.get('apps_sw')
            report_type = request.POST.get('report_type')
            pc_ip = request.POST.get('pc_ip')

            # Get a new recommendation from ChatGPT based on report_desc
            chatgpt_response = get_chatgpt_recommendation(hw_type, apps_sw, report_type, report_desc)

            # Render the same page with the new action
            return render(request, 'chatbot_response.html', {
                'hw_type': hw_type,
                'apps_sw': apps_sw,
                'pc_ip': pc_ip,
                'report_type': report_type,
                'report_desc': report_desc,
                'action': action,
                'form': form,
                'chatgpt_response': chatgpt_response,  # Pass the ChatGPT response to the template
            })

        else:
            # Handle initial form submission
            form = ChatbotForm(request.POST)
            if form.is_valid():
                hw_type = form.cleaned_data['hw_type']
                apps_sw = form.cleaned_data['apps_sw']
                pc_ip = form.cleaned_data['pc_ip']
                report_type = form.cleaned_data['report_type']
                report_desc = form.cleaned_data['report_desc']

                # Step 1: Get recommendation from your model
                action = recommend_action(hw_type, apps_sw, report_type, report_desc)

                # Step 2: Fallback to ChatGPT if no recommendation from your model
                if not action:
                    action = get_chatgpt_recommendation(hw_type, apps_sw, report_type, report_desc)

                # Render the response page with the action (from model or ChatGPT)
                return render(request, 'chatbot_response.html', {
                    'hw_type': hw_type,
                    'apps_sw': apps_sw,
                    'pc_ip': pc_ip,
                    'report_type': report_type,
                    'report_desc': report_desc,
                    'action': action,
                    'form': form,
                })

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
        tickets = Ticket.objects.all()
        return render(request, 'admin_dashboard.html', {"tickets": tickets})
    return redirect('login')

# Technician Dashboard View
@login_required
def technician_dashboard(request):
    if request.user.is_technician:
        return render(request, 'technician_dashboard.html')
    return redirect('login')

@login_required
def open_tickets(request):
    if request.user.is_technician:
        tickets = Ticket.objects.filter(act_stat='O')
        return render(request, 'open_tickets.html', {'tickets': tickets})
    return redirect('login')

@login_required
def update_ticket(request, ticket_id):
    if request.user.is_technician and request.method == 'POST':
        ticket = get_object_or_404(Ticket, id=ticket_id)
        action_taken = request.POST.get('action_taken', '').strip()
        if action_taken:
            ticket.act_taken = action_taken
            ticket.act_stat = 'S'
            ticket.taken_by = request.user.username
        else:
            ticket.act_taken = 'Chatbot'
            ticket.act_stat = 'S'
            ticket.taken_by = 'chatbot'
        ticket.save()
        return redirect('open_tickets')
    return redirect('login')

@login_required
def closed_tickets(request):
    if request.user.is_technician:
        tickets = Ticket.objects.filter(act_stat='S', taken_by=request.user.username)
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
