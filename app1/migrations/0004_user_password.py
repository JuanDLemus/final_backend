# Generated by Django 5.2.1 on 2025-05-16 18:57

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app1', '0003_menuitem_calories_menuitem_category'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='password',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
    ]
