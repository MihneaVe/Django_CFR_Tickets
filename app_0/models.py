from django.db import models
from django.contrib.auth.models import AbstractUser
import uuid

class Tren(models.Model):
    nume = models.CharField(max_length=50)
    tip = models.CharField(max_length=30)
    numar_locuri = models.IntegerField()

    def __str__(self):
        return f"{self.nume} ({self.tip})"

class Vagon(models.Model):
    tip = models.CharField(max_length=30)
    numar_locuri = models.IntegerField()
    tren = models.ForeignKey(Tren, on_delete=models.CASCADE, related_name="vagoane")

    def __str__(self):
        return f"Vagon {self.tip} - Tren: {self.tren.nume}"

class Statie(models.Model):
    nume = models.CharField(max_length=50)
    oras = models.CharField(max_length=50)

    def __str__(self):
        return f"{self.nume}, {self.oras}"

class Ruta(models.Model):
    nume = models.CharField(max_length=50)
    durata = models.DurationField()
    statii = models.ManyToManyField(Statie, related_name="rute")

    def __str__(self):
        return self.nume

class Cursa(models.Model):
    data_plecare = models.DateTimeField()
    data_sosire = models.DateTimeField()
    tren = models.ForeignKey(Tren, on_delete=models.CASCADE, related_name="curse")
    ruta = models.ForeignKey(Ruta, on_delete=models.CASCADE, related_name="curse")

    def __str__(self):
        return f"Cursa {self.tren.nume} pe ruta {self.ruta.nume}"

class Bilet(models.Model):
    pret = models.DecimalField(max_digits=10, decimal_places=2)
    loc = models.CharField(max_length=10)
    vagon = models.ForeignKey(Vagon, on_delete=models.SET_NULL, null=True, related_name="bilete")
    cursa = models.ForeignKey(Cursa, on_delete=models.CASCADE, related_name="bilete")

    def __str__(self):
        return f"Bilet pentru locul {self.loc} - Cursa: {self.cursa}"
    
    @property
    def available_stock(self):
        total_seats = self.vagon.numar_locuri
        sold_tickets = Bilet.objects.filter(vagon=self.vagon, cursa=self.cursa).count()
        return total_seats - sold_tickets

    @property
    def tren(self):
        return self.cursa.tren

    @property
    def ruta(self):
        return self.cursa.ruta

class CustomUser(AbstractUser):
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    address = models.CharField(max_length=255, blank=True, null=True)
    birth_date = models.DateField(blank=True, null=True)
    profile_picture = models.ImageField(upload_to='profile_pictures/', blank=True, null=True)
    bio = models.TextField(blank=True, null=True)
    cod = models.CharField(max_length=100, blank=True, null=True)
    email_confirmat = models.BooleanField(default=False)

    def __str__(self):
        return self.username
    
    class Meta:
        permissions = [
            ("vizualizeaza_oferta", "Can view offer"),
        ]
    
class Vizualizare(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    produs = models.ForeignKey(Bilet, on_delete=models.CASCADE)
    data_vizualizare = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-data_vizualizare']

class Promotie(models.Model):
    nume = models.CharField(max_length=100)
    data_creare = models.DateTimeField(auto_now_add=True)
    data_expirare = models.DateTimeField()
    subiect = models.CharField(max_length=255)
    mesaj = models.TextField()
    categorii = models.ManyToManyField(Vagon)

    def __str__(self):
        return self.nume