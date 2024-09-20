"""
URL configuration for Trial project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from app1 import views
from django.contrib.auth import views as auth_views
#from app1.forms import EmailAuthenticationForm
from app1.views import (
    login_view, logout_view, SignUp, admin_dashboard, technician_dashboard, dashboard_analysis,
    user_dashboard, user_tickets, chatbot_view, open_tickets, update_ticket, closed_tickets
)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.landing_page, name='landing_page'),
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),
    path('signup/', SignUp.as_view(), name='signup'),
    path('admin_dashboard/', admin_dashboard, name='admin_dashboard'),
    path('technician_dashboard', technician_dashboard, name='technician_dashboard'),
    path('user_dashboard', user_dashboard, name='user_dashboard'),
    path('user-tickets/',user_tickets, name='user_tickets'),
    path('chatbot/', chatbot_view, name='chatbot_view'),
    path('open-tickets/', open_tickets, name='open_tickets'),
    path('update-ticket/<int:ticket_id>/', update_ticket, name='update_ticket'),
    path('closed-tickets/', closed_tickets, name='closed_tickets'),
    path('dashboard_analysis/', views.dashboard_analysis, name='dashboard_analysis'),  # New path for analysis

# Password reset views
    path('password_reset/', auth_views.PasswordResetView.as_view(template_name='registration/password_reset_form.html'), name='password_reset'),
    path('password_reset/done/', auth_views.PasswordResetDoneView.as_view(template_name='registration/password_reset_done.html'), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(template_name='registration/password_reset_confirm.html'), name='password_reset_confirm'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(template_name='registration/password_reset_complete.html'), name='password_reset_complete'),
    #path('admin-dashboard/', dashboard_view, name='admin_dashboard_view'),
    #path('technician-dashboard/', dashboard_view, name='technician_dashboard'),
   # path('dashboard/', dashboard_view, name='dashboard_view'),
]

