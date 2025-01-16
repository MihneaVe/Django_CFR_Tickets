from datetime import timedelta
import logging
from django.contrib import messages
from django.core.paginator import Paginator
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from .models import Bilet, CustomUser, Vizualizare
from .forms import BiletFilterForm, BiletForm, ContactForm, CustomUserCreationForm, CustomAuthenticationForm
from django.template.loader import render_to_string
from django.contrib.auth import login, authenticate, logout,update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm
from django.core.mail import send_mass_mail, mail_admins
from app_0 import models
from django.utils import timezone
from django.core.exceptions import PermissionDenied
from django.contrib.auth.decorators import permission_required
from django.contrib.auth.models import Permission

def index(request):
    return render(request, 'app_0/home.html')

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



@permission_required('app_0.add_bilet', raise_exception=True)
def adauga_bilet(request):
    try:
        if request.method == 'POST':
            form = BiletForm(request.POST)
            if form.is_valid():
                form.save()
                return redirect('adauga_bilet_success')
        else:
            form = BiletForm()
        return render(request, 'app_0/adauga_bilet.html', {'form': form})
    except PermissionDenied:
        context = {
            'titlu': 'Eroare adaugare produse',
            'mesaj_personalizat': 'Nu ai voie să adaugi bilete'
        }
        return render(request, 'app_0/403.html', context, status=403)

def adauga_bilet_success(request):
    return render(request, 'app_0/adauga_bilet_success.html')


# LAB 6 TASK 2

def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST, request.FILES)
        if form.is_valid():
            if form.cleaned_data['username'].lower() == 'admin':
                subject = "cineva incearca sa ne preia site-ul"
                message = f"Email: {form.cleaned_data['email']}"
                html_message = f"<h1 style='color:red;'>cineva incearca sa ne preia site-ul</h1><p>Email: {form.cleaned_data['email']}</p>"
                mail_admins(subject, message, html_message=html_message)
                messages.error(request, 'This username is not allowed.')
                logger.critical(f"Attempt to register with username 'admin' from email: {form.cleaned_data['email']}")
                return redirect('register')
            form.save()
            logger.info(f"New user registered: {form.cleaned_data['username']}")
            return redirect('login')
        else:
            logger.error("User registration failed.")
    else:
        form = CustomUserCreationForm()
    return render(request, 'app_0/register.html', {'form': form})

# LAB 6 TASK 3

login_attempts = {}

logger = logging.getLogger('django')

def custom_login(request):
    if request.method == 'POST':
        form = CustomAuthenticationForm(request, data=request.POST)
        username = request.POST.get('username')
        ip_address = request.META.get('REMOTE_ADDR')

        # Track login attempts
        if username not in login_attempts:
            login_attempts[username] = []
        login_attempts[username].append(timezone.now())

        # Remove attempts older than 2 minutes
        login_attempts[username] = [attempt for attempt in login_attempts[username] if attempt > timezone.now() - timedelta(minutes=2)]

        if len(login_attempts[username]) > 3:
            subject = "Logari suspecte"
            message = f"Username: {username}\nIP Address: {ip_address}"
            html_message = f"<h1 style='color:red;'>Logari suspecte</h1><p>Username: {username}</p><p>IP Address: {ip_address}</p>"
            mail_admins(subject, message, html_message=html_message)
            login_attempts[username] = []  # Reset attempts after sending email
            logger.warning(f"Suspicious login attempts for username: {username} from IP: {ip_address}")

        if form.is_valid():
            user = form.get_user()
            if not user.email_confirmat:
                messages.error(request, 'Please confirm your email address before logging in.')
                logger.info(f"User {username} attempted to log in without confirming email.")
                return redirect('login')
            login(request, user)
            if form.cleaned_data.get('remember_me'):
                request.session.set_expiry(86400)  # 1 day
            else:
                request.session.set_expiry(0)  # Browser close
            logger.debug(f"User {username} logged in successfully.")
            return redirect('profile')
        else:
            logger.error(f"Login failed for username: {username}")
    else:
        form = CustomAuthenticationForm()
    return render(request, 'app_0/login.html', {'form': form})

@login_required
def custom_logout(request):
    try:
        permission = Permission.objects.get(codename='vizualizeaza_oferta')
        if request.user.has_perm('app_0.vizualizeaza_oferta'):
            request.user.user_permissions.remove(permission)
    except Permission.DoesNotExist:
        pass  # Handle the case where the permission does not exist
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

# def promotii(request):
#     if request.method == 'POST':
#         form = PromotieForm(request.POST)
#         if form.is_valid():
#             promotie = form.save()
#             bilete = form.cleaned_data['categorii']
#             k = 3  # Minimum number of views to qualify for promotion
#             messages = []
#             for bilet in bilete:
#                 users = CustomUser.objects.filter(
#                     vizualizare__produs=bilet
#                 ).annotate(num_vizualizari=models.Count('vizualizare')).filter(num_vizualizari__gte=k).distinct()
#                 for user in users:
#                     context = {
#                         'subiect': promotie.subiect,
#                         'data_expirare': promotie.data_expirare,
#                         'mesaj': promotie.mesaj,
#                     }
#                     html_message = render_to_string('app_0/email_promo.html', context)
#                     messages.append((promotie.subiect, html_message, 'Da-Boss <test.tweb.node@gmail.com>', [user.email]))
#             send_mass_mail(messages)
#             return redirect('promotii_success')
#     else:
#         form = PromotieForm()
#     return render(request, 'app_0/promotii.html', {'form': form})

# def promotii_success(request):
#     return render(request, 'app_0/promotii_success.html')

def bilet_detail(request, bilet_id):
    bilet = get_object_or_404(Bilet, id=bilet_id)
    
    # Record the view
    if request.user.is_authenticated:
        adauga_vizualizare(request.user, bilet)
    
    return render(request, 'app_0/bilet_detail.html', {'bilet': bilet})

def recent_purchases(request):
    try:
        logger.debug("Starting recent_purchases view.")
        
        # Fetch recent purchases for the logged-in user
        recent_tickets = Bilet.objects.filter(user=request.user).order_by('-purchase_date')[:10]
        logger.info(f"Fetched recent purchases for user: {request.user.username}")
        
        # Check if there are any recent purchases
        if not recent_tickets:
            logger.warning(f"No recent purchases found for user: {request.user.username}")
        
        return render(request, 'app_0/recent_purchases.html', {'recent_tickets': recent_tickets})
    
    except Exception as e:
        subject = "An error occurred in recent_purchases view"
        message = str(e)
        html_message = f"<p style='background-color:red;'>{str(e)}</p>"
        mail_admins(subject, message, html_message=html_message)
        logger.critical(f"An error occurred: {str(e)}")
        return HttpResponse("An error occurred.", status=500)
    

def custom_403_view(request, exception):
    context = {
        'titlu': 'Acces Interzis',
        'mesaj_personalizat': str(exception)
    }
    return render(request, 'app_0/403.html', context)

def test_403(request):
    raise PermissionDenied("You do not have permission to access this resource.")

@login_required
def assign_offer_permission(request):
    permission = Permission.objects.get(codename='vizualizeaza_oferta')
    request.user.user_permissions.add(permission)
    return redirect('oferta_view')

@login_required
def oferta(request):
    if not request.user.has_perm('app_0.vizualizeaza_oferta'):
        context = {
            'titlu': 'Eroare afisare oferta',
            'mesaj_personalizat': 'Nu ai voie să vizualizezi oferta'
        }
        return render(request, 'app_0/403.html', context, status=403)
    return render(request, 'app_0/oferta.html')

    
@login_required
def view_cart(request):
    cart = request.session.get('cart', {})
    cart_items = []
    total_price = 0
    total_quantity = 0

    for bilet_id, quantity in cart.items():
        bilet = get_object_or_404(Bilet, id=bilet_id)
        total_price += bilet.pret * quantity
        total_quantity += quantity
        cart_items.append({
            'bilet': bilet,
            'quantity': quantity,
            'total_price': bilet.pret * quantity
        })

    html = render_to_string('app_0/cart_sidebar.html', {
        'cart_items': cart_items,
        'total_price': total_price,
        'total_quantity': total_quantity
    })

    return JsonResponse({'html': html}, content_type='application/json')
    
@login_required
def cart_page(request):
    cart = request.session.get('cart', {})
    cart_items = []
    total_price = 0
    total_quantity = 0

    for bilet_id, quantity in cart.items():
        bilet = get_object_or_404(Bilet, id=bilet_id)
        total_price += bilet.pret * quantity
        total_quantity += quantity
        cart_items.append({
            'bilet': bilet,
            'quantity': quantity,
            'total_price': bilet.pret * quantity
        })

    context = {
        'cart_items': cart_items,
        'total_price': total_price,
        'total_quantity': total_quantity
    }

    return render(request, 'app_0/cart_page.html', context)

def add_to_cart(request, bilet_id):
    cart = request.session.get('cart', {})
    quantity = int(request.POST.get('quantity', 1))
    bilet = get_object_or_404(Bilet, id=bilet_id)

    if bilet.available_stock >= quantity:
        if bilet_id in cart:
            cart[bilet_id] += quantity
        else:
            cart[bilet_id] = quantity
        request.session['cart'] = cart
        return JsonResponse({'status': 'success', 'message': 'Product added to cart'})
    else:
        return JsonResponse({'status': 'error', 'message': 'Not enough stock available'})

def update_cart(request, bilet_id):
    cart = request.session.get('cart', {})
    quantity = int(request.POST.get('quantity', 1))
    bilet = get_object_or_404(Bilet, id=bilet_id)

    if bilet.available_stock >= quantity:
        cart[bilet_id] = quantity
        request.session['cart'] = cart
        return JsonResponse({'status': 'success', 'message': 'Cart updated'})
    else:
        return JsonResponse({'status': 'error', 'message': 'Not enough stock available'})

def remove_from_cart(request, bilet_id):
    cart = request.session.get('cart', {})
    if bilet_id in cart:
        del cart[bilet_id]
        request.session['cart'] = cart
        return JsonResponse({'status': 'success', 'message': 'Product removed from cart'})
    else:
        return JsonResponse({'status': 'error', 'message': 'Product not in cart'})