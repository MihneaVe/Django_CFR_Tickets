from django import forms
from .models import Bilet, Promotie, Vagon, Statie, CustomUser
from django.core.exceptions import ValidationError
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from datetime import date
import re
from django.core.mail import send_mail, EmailMultiAlternatives
from django.template.loader import render_to_string
import uuid


class BiletFilterForm(forms.Form):
    tren_nume = forms.CharField(required=False, label='Nume Tren')
    categorie = forms.ChoiceField(
        required=False,
        choices=[('', 'Tip loc')] + [(v, v) for v in Vagon.objects.values_list('tip', flat=True).distinct()],
        label='Tip loc'
    )
    min_pret = forms.DecimalField(required=False, label='Pret minim', min_value=0, decimal_places=2)
    max_pret = forms.DecimalField(required=False, label='Pret maxim', min_value=0, decimal_places=2)
    destinatie = forms.ChoiceField(
        required=False,
        choices=[('', 'Destinatie')] + [(s, s) for s in Statie.objects.values_list('oras', flat=True).distinct()],
        label='Destinatie'
    )


class ContactForm(forms.Form):
    TIP_MESAJ_CHOICES = [
        ('reclamatie', 'Reclamatie'),
        ('intrebare', 'Intrebare'),
        ('review', 'Review'),
        ('cerere', 'Cerere'),
        ('programare', 'Programare'),
    ]

    nume = forms.CharField(max_length=10, required=True, label='Nume')
    prenume = forms.CharField(max_length=50, required=False, label='Prenume')
    data_nasterii = forms.DateField(
        required=True,
        label='Data nasterii',
        widget=forms.DateInput(attrs={'type': 'date'})
    )
    email = forms.EmailField(required=True, label='E-mail')
    confirmare_email = forms.EmailField(required=True, label='Confirmare e-mail')
    tip_mesaj = forms.ChoiceField(choices=TIP_MESAJ_CHOICES, required=True, label='Tip mesaj')
    subiect = forms.CharField(max_length=100, required=True, label='Subiect')
    minim_zile_asteptare = forms.IntegerField(min_value=1, required=True, label='Minim zile asteptare')
    mesaj = forms.CharField(widget=forms.Textarea, required=True, label='Mesaj (va rugam sa va semnati la final)')

    def clean(self):
        cleaned_data = super().clean()
        email = cleaned_data.get('email')
        confirmare_email = cleaned_data.get('confirmare_email')
        data_nasterii = cleaned_data.get('data_nasterii')
        mesaj = cleaned_data.get('mesaj')
        nume = cleaned_data.get('nume')
        prenume = cleaned_data.get('prenume')
        subiect = cleaned_data.get('subiect')

        # Validate email confirmation
        if email != confirmare_email:
            raise ValidationError('Emailul si confirmarea emailului nu coincid.')

        # Validate age
        today = date.today()
        age = today.year - data_nasterii.year - ((today.month, today.day) < (data_nasterii.month, data_nasterii.day))
        if age < 18:
            raise ValidationError('Expeditorul trebuie sa fie major.')

        # Validate message length
        words = re.findall(r'\b\w+\b', mesaj)
        if not (5 <= len(words) <= 100):
            raise ValidationError('Mesajul trebuie sa contina intre 5 si 100 cuvinte.')

        # Validate no links in message
        if any(word.startswith(('http://', 'https://')) for word in words):
            raise ValidationError('Mesajul nu poate contine linkuri.')

        # Validate signature
        if not mesaj.strip().endswith(nume):
            raise ValidationError('Mesajul trebuie sa se incheie cu numele utilizatorului.')

        # Validate text fields
        def validate_text_field(value, field_name):
            if value and not re.match(r'^[A-Z][a-zA-Z\s]*$', value):
                raise ValidationError(f'{field_name} trebuie sa inceapa cu litera mare si sa contina doar litere si spatii.')

        validate_text_field(nume, 'Nume')
        validate_text_field(prenume, 'Prenume')
        validate_text_field(subiect, 'Subiect')

        return cleaned_data

    def save(self):
        import json
        import os
        from time import time

        data = self.cleaned_data
        data.pop('confirmare_email')

        # Calculate age in years and months
        today = date.today()
        birth_date = data['data_nasterii']
        age_years = today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))
        age_months = today.month - birth_date.month - (today.day < birth_date.day)
        if age_months < 0:
            age_months += 12
            age_years -= 1
        data['varsta'] = f"{age_years} ani si {age_months} luni"

        # Preprocess message
        mesaj = data['mesaj']
        mesaj = re.sub(r'\s+', ' ', mesaj.replace('\n', ' ')).strip()
        data['mesaj'] = mesaj

        # Convert date to string
        data['data_nasterii'] = birth_date.strftime('%Y-%m-%d')

        # Save to JSON file
        timestamp = int(time())
        filename = f"mesaj_{timestamp}.json"
        folder_path = os.path.join(os.path.dirname(__file__), 'mesaje')
        os.makedirs(folder_path, exist_ok=True)
        filepath = os.path.join(folder_path, filename)

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
            





class BiletForm(forms.ModelForm):
    discount = forms.DecimalField(max_digits=5, decimal_places=2, required=False, label='Discount (%)', help_text='Introduceti un discount in procente.')
    pret_final = forms.DecimalField(max_digits=10, decimal_places=2, required=False, label='Pret final')

    class Meta:
        model = Bilet
        fields = ['loc', 'cursa', 'vagon', 'pret', 'discount', 'pret_final']
        labels = {
            'loc': 'Loc',
            'cursa': 'Cursa',
            'vagon': 'Vagon',
            'pret': 'Pret',
        }
        help_texts = {
            'loc': 'Introduceti locul pentru bilet.',
        }
        error_messages = {
            'loc': {
                'max_length': 'Locul nu poate depasi 10 caractere.',
                'required': 'Locul este obligatoriu.',
            },
            'cursa': {
                'required': 'Cursa este obligatorie.',
            },
            'vagon': {
                'required': 'Vagonul este obligatoriu.',
            },
            'pret': {
                'required': 'Pretul este obligatoriu.',
            },
        }

    def clean_discount(self):
        discount = self.cleaned_data.get('discount')
        if discount is not None and (discount < 0 or discount > 100):
            raise ValidationError('Discountul trebuie sa fie intre 0 si 100%.')
        return discount

    def clean_pret_final(self):
        pret_final = self.cleaned_data.get('pret_final')
        if pret_final is not None and pret_final <= 0:
            raise ValidationError('Pretul final trebuie sa fie mai mare decat 0.')
        return pret_final

    def clean(self):
        cleaned_data = super().clean()
        discount = cleaned_data.get('discount')
        pret_final = cleaned_data.get('pret_final')

        if discount is not None and pret_final is not None:
            raise ValidationError('Nu puteti introduce atat discount cat si pret final. Alegeti una dintre optiuni.')

        return cleaned_data

    def save(self, commit=True):
        bilet = super().save(commit=False)
        discount = self.cleaned_data.get('discount')
        pret_final = self.cleaned_data.get('pret_final')

        if discount is not None:
            bilet.pret = bilet.pret * (1 - discount / 100)
        elif pret_final is not None:
            bilet.pret = pret_final

        if commit:
            bilet.save()
        return bilet
    
    
# LAB 6 TASK 2

class CustomUserCreationForm(UserCreationForm):
    phone_number = forms.CharField(max_length=15, required=False, label='Phone Number')
    address = forms.CharField(max_length=255, required=False, label='Address')
    birth_date = forms.DateField(
        required=False,
        label='Birth Date',
        widget=forms.DateInput(attrs={'type': 'date'})
    )
    profile_picture = forms.ImageField(required=False, label='Profile Picture')
    bio = forms.CharField(widget=forms.Textarea, required=False, label='Bio')

    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'phone_number', 'address', 'birth_date', 'profile_picture', 'bio', 'password1', 'password2']

    def clean_phone_number(self):
        phone_number = self.cleaned_data.get('phone_number')
        if phone_number and not re.match(r'^\+?1?\d{9,15}$', phone_number):
            raise ValidationError('Enter a valid phone number.')
        return phone_number

    def clean_birth_date(self):
        birth_date = self.cleaned_data.get('birth_date')
        if birth_date and birth_date > date.today():
            raise ValidationError('Birth date cannot be in the future.')
        return birth_date

    def clean_bio(self):
        bio = self.cleaned_data.get('bio')
        if bio and len(bio.split()) > 100:
            raise ValidationError('Bio cannot exceed 100 words.')
        return bio

    def save(self, commit=True):
        user = super().save(commit=False)
        user.cod = str(uuid.uuid4())
        if commit:
            user.save()
            self.send_confirmation_email(user)
        return user

    def send_confirmation_email(self, user):
        subject = 'Confirm your email address'
        html_content = render_to_string('app_0/email_confirmation.html', {
            'user': user,
            'confirmation_url': f"http://localhost:8000/index/confirma_mail/{user.cod}/"
        })
        text_content = f"""
        Welcome to our site, {user.first_name} {user.last_name}!
        Thank you for registering on our site. Please confirm your email address by clicking the link below:
        {f"http://localhost:8000/index/confirma_mail/{user.cod}/"}
        Username: {user.username}
        """
        email = EmailMultiAlternatives(subject, text_content, 'Da-Boss <test.tweb.node@gmail.com>', [user.email])
        email.attach_alternative(html_content, "text/html")
        email.send()
    
# LAB 6 TASK 3
class CustomAuthenticationForm(AuthenticationForm):
    remember_me = forms.BooleanField(required=False, label='Remember Me')
    

# class PromotieForm(forms.ModelForm):
#     categorii = forms.ModelMultipleChoiceField(
#         queryset=Bilet.objects.all(),
#         widget=forms.CheckboxSelectMultiple,
#         required=True,
#         label='Bilete'
#     )

#     class Meta:
#         model = Promotie
#         fields = ['nume', 'data_expirare', 'subiect', 'mesaj', 'categorii']