# Generated by Django 5.1.1 on 2025-01-15 15:56

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app_0', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='customuser',
            name='cod',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
        migrations.AddField(
            model_name='customuser',
            name='email_confirmat',
            field=models.BooleanField(default=False),
        ),
    ]
