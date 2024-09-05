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
from openai.error import RateLimitError
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
from django.contrib.auth.decorators import login_required
from .forms import ChatbotForm
from .models import Ticket
from .chatbot import recommend_action, update_model_with_new_data
import openai
import logging

# Set up logging
logger = logging.getLogger(__name__)

# Chatbot View
@login_required
def chatbot_view(request):
    form = ChatbotForm()
    action = None
    chatgpt_response = None

    if request.method == 'POST':
        # Handle feedback submission after action recommendation
        if 'submit_feedback' in request.POST:
            # Extract data from the form
            resolved = request.POST.get('resolved', None)
            dprt = request.POST.get('dprt')
            post = request.POST.get('post')
            env = request.POST.get('env')
            hw_type = request.POST.get('hw_type')
            apps_sw = request.POST.get('apps_sw')
            report_type = request.POST.get('report_type')
            report_desc = request.POST.get('report_desc')
            pc_ip = request.POST.get('pc_ip')
            pc_name = f"{dprt}-{post}-{env}"  # Auto-generate pc_name
            action = request.POST.get('action')

            # Check if the user marked the issue as resolved or not
            act_stat = 'S' if resolved == 'yes' else 'O'

            # Save the feedback as a Ticket in the database
            Ticket.objects.create(
                dprt=dprt,
                post=post,
                env=env,
                hw_type=hw_type,
                apps_sw=apps_sw,
                report_type=report_type,
                report_desc=report_desc,
                pc_ip=pc_ip,
                act_taken=action,
                act_stat=act_stat,
                user_name=request.user.username,
                email=request.user.email,
                pc_name=pc_name,
                taken_by='chatbot',
            )

            # Redirect to a confirmation page or chatbot view after saving the feedback
            return redirect('chatbot_view')

        # Handle generating new action from ChatGPT
        elif 'generate_new_action' in request.POST:
            report_desc = request.POST.get('report_desc')
            hw_type = request.POST.get('hw_type')
            apps_sw = request.POST.get('apps_sw')
            report_type = request.POST.get('report_type')
            pc_ip = request.POST.get('pc_ip')

            # Generate new recommendation from ChatGPT
            chatgpt_response = get_chatgpt_recommendation(hw_type, apps_sw, report_type, report_desc)

            # Render the response page with the new ChatGPT action
            return render(request, 'chatbot_response.html', {
                'hw_type': hw_type,
                'apps_sw': apps_sw,
                'pc_ip': pc_ip,
                'report_type': report_type,
                'report_desc': report_desc,
                'action': request.POST.get('action', ''),  # Preserve the original action
                'form': form,
                'chatgpt_response': chatgpt_response,
            })

        # Initial form submission
        else:
            form = ChatbotForm(request.POST)
            if form.is_valid():
                dprt = form.cleaned_data.get('dprt')
                post = form.cleaned_data.get('post')
                env = form.cleaned_data.get('env')
                hw_type = form.cleaned_data.get('hw_type')
                apps_sw = form.cleaned_data.get('apps_sw')
                pc_ip = form.cleaned_data.get('pc_ip')
                report_type = form.cleaned_data.get('report_type')
                report_desc = form.cleaned_data.get('report_desc')
                pc_name = f"{dprt}-{post}-{env}"

                # Get recommendation from the model or fallback to ChatGPT
                action = recommend_action(hw_type, apps_sw, report_type, report_desc)
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

# Function to call ChatGPT and get recommendation
def get_chatgpt_recommendation(hw_type, apps_sw, report_type, report_desc):
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",  # Or use gpt-4 depending on your plan
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
        logger.error("OpenAI RateLimitError: Too many requests.")
        return "We're experiencing high traffic. Please try again later."


    except Exception as e:
        logger.error(f"OpenAI API Error: {e}")
        return "Error processing request with ChatGPT. Please try again later."



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
from django.shortcuts import render
from .models import Ticket
from django.db.models import Q


@login_required
def admin_dashboard(request):
    tickets = Ticket.objects.all()

    # Filtering
    report_type = request.GET.get('report_type')
    act_stat = request.GET.get('act_stat')
    taken_by = request.GET.get('taken_by')

    if report_type:
        tickets = tickets.filter(report_type=report_type)
    if act_stat:
        tickets = tickets.filter(act_stat=act_stat)
    if taken_by:
        tickets = tickets.filter(taken_by=taken_by)

    # Sorting
    sort_by = request.GET.get('sort_by', 'user_name')
    sort_order = request.GET.get('sort_order', 'asc')

    if sort_order == 'asc':
        tickets = tickets.order_by(sort_by)
    else:
        tickets = tickets.order_by(f'-{sort_by}')

    context = {
        'tickets': tickets,
        'report_type': report_type,
        'act_stat': act_stat,
        'taken_by': taken_by,
        'sort_by': sort_by,
        'sort_order': sort_order,
    }

    return render(request, 'admin_dashboard.html', context)


# Technician Dashboard View
@login_required
def technician_dashboard(request):
    if request.user.is_technician:
        return render(request, 'technician_dashboard.html')
    return redirect('login')

@login_required
def open_tickets(request):
    if request.user.is_technician:
        tickets = Ticket.objects.filter(act_stat='O') #()
        return render(request, 'open_tickets.html', {'tickets': tickets})
    return redirect('login')

@login_required
@login_required
def update_ticket(request, ticket_id):
    # Ensure only technician can update the ticket
    if not request.user.is_technician:
        return redirect('login')  # Redirect to login if not a technician

    # Fetch the ticket based on ID
    ticket = get_object_or_404(Ticket, id=ticket_id)

    if request.method == 'POST':
        # Process the form submission
        action_taken = request.POST.get('action_taken', '').strip()
        act_stat = request.POST.get('act_stat', '').strip()

        if action_taken:
            ticket.act_taken = action_taken
            ticket.act_stat = act_stat if act_stat else 'S'  # Default to 'S' if no status provided
            ticket.taken_by = request.user.username
        else:
            ticket.act_taken = 'Chatbot'
            ticket.act_stat = 'S'
            ticket.taken_by = 'chatbot'

        ticket.save()
        return redirect('open_tickets')

    # Render the update_ticket.html template
    return render(request, 'update_ticket.html', {'ticket': ticket})


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

def get_chatgpt_response(messages):
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages,
        temperature=1,
        max_tokens=256,
        top_p=1,
        frequency_penalty=0,
        presence_penalty=0,
        response_format={"type": "text"}
    )
    return response['choices'][0]['message']['content'].strip()