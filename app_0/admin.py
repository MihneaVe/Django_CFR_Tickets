from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Promotie, Tren, Vagon, Statie, Ruta, Cursa, Bilet, CustomUser, Vizualizare

# Customizing the admin site
admin.site.site_header = "Administrație Trenuri"
admin.site.site_title = "Administrație Trenuri"
admin.site.index_title = "Bine ați venit la Administrația Trenuri"

# Customizing the admin interface for the Tren model
@admin.register(Tren)
class TrenAdmin(admin.ModelAdmin):
    list_display = ('nume', 'tip', 'numar_locuri')
    search_fields = ('nume',)
    list_filter = ('tip',)
    fieldsets = (
        ('General Info', {
            'fields': ('nume', 'tip')
        }),
        ('Capacity', {
            'fields': ('numar_locuri',)
        }),
    )

# Customizing the admin interface for the Vagon model
@admin.register(Vagon)
class VagonAdmin(admin.ModelAdmin):
    list_display = ('tip', 'numar_locuri', 'tren')
    search_fields = ('tip',)
    list_filter = ('tip', 'tren')

# Customizing the admin interface for the Statie model
@admin.register(Statie)
class StatieAdmin(admin.ModelAdmin):
    list_display = ('nume', 'oras')
    search_fields = ('nume',)
    list_filter = ('oras',)

# Customizing the admin interface for the Ruta model
@admin.register(Ruta)
class RutaAdmin(admin.ModelAdmin):
    list_display = ('nume', 'durata')
    search_fields = ('nume',)
    list_filter = ('durata',)

# Customizing the admin interface for the Cursa model
@admin.register(Cursa)
class CursaAdmin(admin.ModelAdmin):
    list_display = ('data_plecare', 'data_sosire', 'tren', 'ruta')
    search_fields = ('tren__nume', 'ruta__nume')
    list_filter = ('data_plecare', 'data_sosire', 'tren', 'ruta')

# Customizing the admin interface for the Bilet model
@admin.register(Bilet)
class BiletAdmin(admin.ModelAdmin):
    list_display = ('pret', 'loc', 'vagon', 'cursa')
    search_fields = ('loc',)
    list_filter = ('pret', 'vagon', 'cursa')

@admin.register(Promotie)
class PromotieAdmin(admin.ModelAdmin):
    list_display = ('nume', 'data_creare', 'data_expirare', 'subiect')
    search_fields = ('nume', 'subiect')
    list_filter = ('data_creare', 'data_expirare')

@admin.register(Vizualizare)
class VizualizareAdmin(admin.ModelAdmin):
    list_display = ('user', 'produs', 'data_vizualizare')
    search_fields = ('user__username', 'produs__nume')
    list_filter = ('data_vizualizare',)


class CustomUserAdmin(UserAdmin):
    fieldsets = (
        *UserAdmin.fieldsets,
        (
            'Additional Info',
            {
                'fields': (
                    'phone_number',
                    'address',
                    'birth_date',
                    'profile_picture',
                    'bio',
                    'email_confirmat',
                ),
            },
        ),
    )
    add_fieldsets = (
        *UserAdmin.add_fieldsets,
        (
            'Additional Info',
            {
                'fields': (
                    'phone_number',
                    'address',
                    'birth_date',
                    'profile_picture',
                    'bio',
                ),
            },
        ),
    )

try:
    admin.site.unregister(CustomUser)
except admin.sites.NotRegistered:
    pass

admin.site.register(CustomUser, CustomUserAdmin)
#User - mihnea
#Pass - 1234