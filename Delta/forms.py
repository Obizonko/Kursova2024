from django import forms
from Teta.models import Users, Organizations, OrganizationMembers, Events, Roles, Participants
from django.contrib.auth.forms import AuthenticationForm
from django.forms.widgets import SelectDateWidget
from django.forms import formset_factory, modelformset_factory
from django.contrib.auth.password_validation import validate_password
from django.core.validators import MinLengthValidator
from django.core.exceptions import ValidationError


class EventRegistrationForm(forms.ModelForm):
    role = forms.ModelChoiceField(queryset=Roles.objects.none(), required=False, label='Role')

    class Meta:
        model = Participants
        fields = ['role']

    def __init__(self, *args, **kwargs):
        event = kwargs.pop('event', None)
        super(EventRegistrationForm, self).__init__(*args, **kwargs)
        if event:
            self.fields['role'].queryset = Roles.objects.filter(event=event)

class UserRegistrationForm(forms.ModelForm):
    password = forms.CharField(
        widget=forms.PasswordInput,
        label='Password',
        validators=[MinLengthValidator(8), validate_password]
    )
    password2 = forms.CharField(widget=forms.PasswordInput, label='Confirm Password')
    gender = forms.ChoiceField(
        choices=[('male', 'Male'), ('female', 'Female')],
        widget=forms.RadioSelect,
        label='Gender'
    )
    birth_date = forms.DateField(
        widget=forms.SelectDateWidget(years=range(1900, 2024)),
        label='Birth Date'
    )

    class Meta:
        model = Users
        fields = ['name', 'surname', 'email', 'gender', 'birth_date', 'password']

    def clean_password2(self):
        password = self.cleaned_data.get('password')
        password2 = self.cleaned_data.get('password2')
        if password and password2 and password != password2:
            raise forms.ValidationError('Passwords do not match.')
        return password2

    def clean_password(self):
        password = self.cleaned_data.get('password')
        try:
            validate_password(password)
        except ValidationError as e:
            raise forms.ValidationError(e)
        return password

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password'])
        if commit:
            user.save()
        return user

class UserLoginForm(AuthenticationForm):
    username = forms.CharField(label='Електронна пошта', widget=forms.TextInput(
        attrs={'class': 'form-control', 'placeholder': 'Введіть електронну пошту'}))
    password = forms.CharField(label='Пароль', widget=forms.PasswordInput(
        attrs={'class': 'form-control', 'placeholder': 'Введіть пароль'}))



class OrganizationForm(forms.ModelForm):
    class Meta:
        model = Organizations
        fields = ['name', 'description', 'logo_photo_url']

class EventForm(forms.ModelForm):
    class Meta:
        model = Events
        fields = ['organization', 'event_name', 'description', 'location', 'start_time', 'end_time', 'banner', 'max_participants']
        widgets = {
            'start_time': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'end_time': forms.DateTimeInput(attrs={'type': 'datetime-local'})
        }

RoleFormSet = modelformset_factory(Roles, fields=['role', 'description', 'allowed_number_of_users'], extra=1)


class RoleForm(forms.ModelForm):
    user_email = forms.EmailField(required=False, label='Email учасника')

    class Meta:
        model = Roles
        fields = ['role', 'description', 'allowed_number_of_users', 'user_email']


RoleFormSet = formset_factory(RoleForm, extra=1)
class ParticipantRegistrationForm(forms.ModelForm):
    email = forms.EmailField(label='User Email')

    class Meta:
        model = Participants
        fields = []

    def __init__(self, *args, **kwargs):
        event = kwargs.pop('event', None)
        super().__init__(*args, **kwargs)
        if event:
            self.fields['role'] = forms.ModelChoiceField(
                queryset=Roles.objects.filter(event=event),
                required=False
            )