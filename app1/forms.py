from django import forms
from .models import Ticket

from django import forms
from .models import Ticket

class ChatbotForm(forms.Form):
    username = forms.CharField(
        label='Nama Pegawai',
        required=True,
        widget=forms.TextInput(attrs={'readonly': 'readonly', 'class': 'form-control'})
    )
    dprt = forms.ChoiceField(
        label='Department',
        choices=[('', 'Sila Pilih')],  # Populate in the view
        required=True,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    post = forms.ChoiceField(
        label='Jawatan',
        choices=[('', 'Sila Pilih')], # Populate in the view
        required=True,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    env = forms.ChoiceField(
        label='Persekitaran',
        choices=[('', 'Sila Pilih')], # Populate in the view
        required=True,
        widget=forms.Select(attrs={'class': 'form-control',})
    )
    pc_ip = forms.CharField(
        label='Alamat IP Komputer',
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Masukkan Alamat IP Komputer'})
    )
    report_type = forms.ChoiceField(
        label='Jenis Laporan',
        choices=[('', 'Sila Pilih')],
        required=True,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    hw_type = forms.ChoiceField(
        label='Jenis Perkakasan',
        choices=[('', 'Sila Pilih')],  # Choices will be set in the view
        required=True,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    apps_sw = forms.ChoiceField(
        label='Perisian/Aplikasi',
        choices=[('', 'Sila Pilih')],
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    report_desc = forms.CharField(
        label='Deskripsi Masalah',
        widget=forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'Jelaskan Masalah Anda Secara Terperinci'}),
        required=True
    )

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super(ChatbotForm, self).__init__(*args, **kwargs)
        if user:
            self.fields['username'].initial = user.username
        self.fields['hw_type'].choices = self.get_distinct_choices('hw_type')
        self.fields['apps_sw'].choices = self.get_distinct_choices('apps_sw')
        self.fields['report_type'].choices = self.get_distinct_choices('report_type')
        self.fields['dprt'].choices = self.get_distinct_choices('dprt')
        self.fields['post'].choices = self.get_distinct_choices('post')
        self.fields['env'].choices = self.get_distinct_choices('env')

    def get_distinct_choices(self, field_name):
        distinct_values = Ticket.objects.values_list(field_name, flat=True).distinct()
        return [(value, value) for value in distinct_values if value]


# forms.py
from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django.contrib.auth import get_user_model

class CustomUserCreationForm(UserCreationForm):
    is_admin = forms.BooleanField(required=False, initial=False, label='Admin')
    is_technician = forms.BooleanField(required=False, initial=False, label='Technician')
    is_user = forms.BooleanField(required=False, initial=True, label='User')  # Default to User

    class Meta:
        model = get_user_model()
        fields = ('username', 'email', 'is_admin', 'is_technician', 'is_user')

    def clean(self):
        cleaned_data = super().clean()
        is_admin = cleaned_data.get('is_admin')
        is_technician = cleaned_data.get('is_technician')
        is_user = cleaned_data.get('is_user')

        if sum([bool(is_admin), bool(is_technician), bool(is_user)]) != 1:
            raise forms.ValidationError("Sila Pilih Satu Peranan Sahaja.")

        return cleaned_data

class CustomUserChangeForm(UserChangeForm):
    class Meta:
        model = get_user_model()
        fields = ('username', 'email')






