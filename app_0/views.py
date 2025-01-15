from pyexpat.errors import messages
from django.core.paginator import Paginator
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from .models import Bilet, CustomUser, Vizualizare
from .forms import BiletFilterForm, BiletForm, ContactForm, CustomUserCreationForm, CustomAuthenticationForm, PromotieForm
from django.template.loader import render_to_string
from django.contrib.auth import login, authenticate, logout,update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm
from django.core.mail import send_mass_mail
from app_0 import models

def index(request):
    return HttpResponse("Hello, world. You're at the polls index.")

def lista_bilete(request):
    form = BiletFilterForm(request.GET)
    queryset = Bilet.objects.all()

    if form.is_valid():
        tren_nume = form.cleaned_data.get('tren_nume')
        if tren_nume:
            queryset = queryset.filter(cursa__tren__nume__icontains=tren_nume)

        categorie = form.cleaned_data.get('categorie')
        if categorie:
            queryset = queryset.filter(vagon__tip=categorie)

        min_pret = form.cleaned_data.get('min_pret')
        if min_pret is not None:
            queryset = queryset.filter(pret__gte=min_pret)

        max_pret = form.cleaned_data.get('max_pret')
        if max_pret is not None:
            queryset = queryset.filter(pret__lte=max_pret)

        destinatie = form.cleaned_data.get('destinatie')
        if destinatie:
            queryset = queryset.filter(cursa__ruta__statii__oras__icontains=destinatie).distinct()

    paginator = Paginator(queryset, 10)  # 10 items per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({
            'html': render_to_string('app_0/bilete_list.html', {'page_obj': page_obj})
        })

    return render(request, 'app_0/lista_bilete.html', {'form': form, 'page_obj': page_obj})

def cumpara_bilet(request, bilet_id):
    bilet = get_object_or_404(Bilet, id=bilet_id)
    # Logic to handle ticket purchase
    # For example, mark the ticket as sold or reduce the available seats
    # Redirect to a success page or back to the ticket list
    return redirect('lista_bilete')

def contact(request):
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('contact_success')
    else:
        form = ContactForm()
    return render(request, 'app_0/contact.html', {'form': form})

def contact_success(request):
    return render(request, 'app_0/contact_success.html')



def adauga_bilet(request):
    if request.method == 'POST':
        form = BiletForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('adauga_bilet_success')
    else:
        form = BiletForm()
    return render(request, 'app_0/adauga_bilet.html', {'form': form})

def adauga_bilet_success(request):
    return render(request, 'app_0/adauga_bilet_success.html')


# LAB 6 TASK 2

def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('login')
    else:
        form = CustomUserCreationForm()
    return render(request, 'app_0/register.html', {'form': form})

# LAB 6 TASK 3

def custom_login(request):
    if request.method == 'POST':
        form = CustomAuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            if not user.email_confirmat:
                messages.error(request, 'Please confirm your email address before logging in.')
                return redirect('login')
            login(request, user)
            if form.cleaned_data.get('remember_me'):
                request.session.set_expiry(86400)  # 1 day
            else:
                request.session.set_expiry(0)  # Browser close
            return redirect('profile')
    else:
        form = CustomAuthenticationForm()
    return render(request, 'app_0/login.html', {'form': form})

@login_required
def custom_logout(request):
    logout(request)
    return redirect('login')

@login_required
def profile(request):
    return render(request, 'app_0/profile.html')

@login_required
def change_password(request):
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)  # Important!
            return redirect('profile')
    else:
        form = PasswordChangeForm(request.user)
    return render(request, 'app_0/change_password.html', {'form': form})

def confirma_mail(request, cod):
    user = get_object_or_404(CustomUser, cod=cod)
    user.email_confirmat = True
    user.cod = None
    user.save()
    return render(request, 'app_0/email_confirmed.html')


def adauga_vizualizare(user, produs):
    vizualizari = Vizualizare.objects.filter(user=user)
    if vizualizari.count() >= 5:
        vizualizari.last().delete()
    Vizualizare.objects.create(user=user, produs=produs)

def promotii(request):
    if request.method == 'POST':
        form = PromotieForm(request.POST)
        if form.is_valid():
            promotie = form.save()
            bilete = form.cleaned_data['categorii']
            k = 3  # Minimum number of views to qualify for promotion
            messages = []
            for bilet in bilete:
                users = CustomUser.objects.filter(
                    vizualizare__produs=bilet
                ).annotate(num_vizualizari=models.Count('vizualizare')).filter(num_vizualizari__gte=k).distinct()
                for user in users:
                    context = {
                        'subiect': promotie.subiect,
                        'data_expirare': promotie.data_expirare,
                        'mesaj': promotie.mesaj,
                    }
                    html_message = render_to_string('app_0/email_promo.html', context)
                    messages.append((promotie.subiect, html_message, 'Da-Boss <test.tweb.node@gmail.com>', [user.email]))
            send_mass_mail(messages)
            return redirect('promotii_success')
    else:
        form = PromotieForm()
    return render(request, 'app_0/promotii.html', {'form': form})

def promotii_success(request):
    return render(request, 'app_0/promotii_success.html')

def bilet_detail(request, bilet_id):
    bilet = get_object_or_404(Bilet, id=bilet_id)
    
    # Record the view
    if request.user.is_authenticated:
        adauga_vizualizare(request.user, bilet)
    
    return render(request, 'app_0/bilet_detail.html', {'bilet': bilet})