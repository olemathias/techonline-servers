# Generated by Django 3.1.6 on 2021-03-13 21:18

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('task', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='entry',
            name='entry_type',
            field=models.PositiveSmallIntegerField(choices=[(1, 'Dhcp Dns'), (2, 'Gondul')]),
        ),
    ]
