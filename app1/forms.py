from django import forms
from .models import Ticket

class ChatbotForm(forms.Form):
    # User Profile Section
    user_name = forms.CharField(
        label='Nama Pegawai',
        required=True,
        widget=forms.TextInput(attrs={'placeholder': 'Masukkan nama', 'class': 'form-control'})  # Automatically populated and read-only
    )
    dprt = forms.ChoiceField(
        label='Bahagian',
        choices=[],  # Will be populated in the view
        widget=forms.Select(attrs={'class': 'form-control', 'id': 'id_dprt'})  # Added 'id' for JavaScript access
    )
    post = forms.ChoiceField(
        label='Jawatan',
        choices=[],  # Will be populated in the view
        widget=forms.Select(attrs={'class': 'form-control', 'id': 'id_post'})  # Added 'id' for JavaScript access
    )
    env = forms.ChoiceField(
        label='Persekitaraan',
        choices=[],  # Will be populated in the view
        widget=forms.Select(attrs={'class': 'form-control', 'id': 'id_env'})  # Added 'id' for JavaScript access
    )
    pc_name = forms.CharField(
        label='Nama PC',
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'readonly': 'readonly', 'id': 'id_pc_name'})  # Auto-populated and read-only
    )

    # Hardware Section
    pc_ip = forms.CharField(
        label='PC IP Address',
        required=True,
        widget=forms.TextInput(attrs={'placeholder': 'Enter PC IP Address', 'class': 'form-control'})
    )
    report_type = forms.ChoiceField(
        label='Jenis Laporan',
        choices=[('hw', 'Hardware Issue'), ('sw', 'Software Issue')],  # Updated to static choices for simplicity
        required=True,
        widget=forms.Select(attrs={'class': 'form-control', 'id': 'id_report_type'})  # Added 'id' for JavaScript access
    )

    hw_type = forms.ChoiceField(
        label='Jenis Perkakasan',
        choices=[],  # Will be set in the view
        required=False,  # Initially not required, only when report_type is hw
        widget=forms.Select(attrs={'class': 'form-control', 'id': 'id_hw_type'})
    )
    apps_sw = forms.ChoiceField(
        label='Software/Application',
        choices=[],  # Will be set in the view
        required=False,  # Initially not required, only when report_type is sw
        widget=forms.Select(attrs={'class': 'form-control', 'id': 'id_apps_sw'})
    )

    # Report Section
    report_desc = forms.CharField(
        label='Deskripsi Masalah',
        widget=forms.Textarea(attrs={'placeholder': 'Describe the issue...', 'class': 'form-control'}),
        required=True
    )

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)  # Get the user from the view
        super(ChatbotForm, self).__init__(*args, **kwargs)

        # Populate the dropdown choices dynamically
        self.fields['hw_type'].choices = self.get_distinct_choices('hw_type')
        self.fields['apps_sw'].choices = self.get_distinct_choices('apps_sw')
        self.fields['dprt'].choices = self.get_distinct_choices('dprt')
        self.fields['post'].choices = self.get_distinct_choices('post')
        self.fields['env'].choices = self.get_distinct_choices('env')

        # Set the username field to the logged-in user's name
        if user:
            self.fields['user_name'].initial = user.username

        # Auto-populate the pc_name field based on dprt, post, and env if available
        if 'dprt' in self.data and 'post' in self.data and 'env' in self.data:
            self.fields['pc_name'].initial = f"{self.data['dprt']}-{self.data['post']}-{self.data['env']}"
        elif user:
            # You can use user profile data to set pc_name if available
            profile = getattr(user, 'userprofile', None)
            if profile:
                self.fields['pc_name'].initial = f"{profile.dprt}-{profile.post}-{profile.env}"

    def get_distinct_choices(self, field_name):
        distinct_values = Ticket.objects.values_list(field_name, flat=True).distinct()
        return [(value, value) for value in distinct_values if value]



# User Creation Form with Roles
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django.contrib.auth import get_user_model

class CustomUserCreationForm(UserCreationForm):
    is_admin = forms.BooleanField(required=False, initial=False, label='Admin', widget=forms.CheckboxInput())
    is_technician = forms.BooleanField(required=False, initial=False, label='Technician', widget=forms.CheckboxInput())
    is_user = forms.BooleanField(required=False, initial=True, label='User', widget=forms.CheckboxInput())

    class Meta:
        model = get_user_model()
        fields = ('username', 'email', 'is_admin', 'is_technician', 'is_user')

    def clean(self):
        cleaned_data = super().clean()
        is_admin = cleaned_data.get('is_admin')
        is_technician = cleaned_data.get('is_technician')
        is_user = cleaned_data.get('is_user')

        if sum([bool(is_admin), bool(is_technician), bool(is_user)]) != 1:
            raise forms.ValidationError("You must select exactly one role.")

        return cleaned_data


class CustomUserChangeForm(UserChangeForm):
    class Meta:
        model = get_user_model()
        fields = ('username', 'email')
