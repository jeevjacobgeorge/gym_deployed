# Generated by Django 5.0.6 on 2025-01-23 15:05

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('gym', '0020_alter_customer_phone_no_alter_feedetail_month_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='customer',
            name='phone_no',
            field=models.CharField(blank=True, max_length=13),
        ),
    ]
