# Generated by Django 4.2 on 2023-04-25 11:16

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('store', '0003_variation'),
    ]

    operations = [
        migrations.AlterField(
            model_name='variation',
            name='variation_category',
            field=models.CharField(choices=[('size', 'size')], max_length=100),
        ),
    ]