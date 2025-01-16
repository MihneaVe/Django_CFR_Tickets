from django.urls import path
from app_0 import views


urlpatterns = [
    path('', views.index, name='index'),
    path('bilete/', views.lista_bilete, name='lista_bilete'),
    path('cumpara-bilet/<int:bilet_id>/', views.cumpara_bilet, name='cumpara_bilet'),
    path('contact/', views.contact, name='contact'),
    path('contact/success/', views.contact_success, name='contact_success'),
    path('adauga-bilet/', views.adauga_bilet, name='adauga_bilet'),
    path('adauga-bilet/success/', views.adauga_bilet_success, name='adauga_bilet_success'),
    path('register/', views.register, name='register'),
    path('login/', views.custom_login, name='login'),
    path('logout/', views.custom_logout, name='logout'),
    path('profile/', views.profile, name='profile'),
    path('change-password/', views.change_password, name='change_password'),
    path('confirma_mail/<str:cod>/', views.confirma_mail, name='confirma_mail'),
    # path('promotii/', views.promotii, name='promotii'),
    # path('promotii/success/', views.promotii_success, name='promotii_success'),
    path('bilet/<int:bilet_id>/', views.bilet_detail, name='bilet_detail'),
    path('recent_purchases/', views.recent_purchases, name='recent_purchases'),
    path('test_403/', views.test_403, name='test_403'),
    path('assign_offer_permission/', views.assign_offer_permission, name='assign_offer_permission'),
    path('oferta/', views.oferta, name='oferta'),
]
