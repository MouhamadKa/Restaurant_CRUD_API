# Generated by Django 5.0.4 on 2024-04-23 06:35

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('LittleLemonAPI', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='cart',
            name='price',
            field=models.DecimalField(decimal_places=2, max_digits=6, null=True),
        ),
        migrations.AlterField(
            model_name='cart',
            name='unit_price',
            field=models.DecimalField(decimal_places=2, max_digits=6, null=True),
        ),
    ]
