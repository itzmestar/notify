# Generated by Django 2.0.5 on 2018-06-09 11:39

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('fcm_django', '0003_auto_20170313_1314'),
        ('alerts', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='vehicle',
            name='imei',
            field=models.CharField(db_index=True, max_length=20, verbose_name='IMEI'),
        ),
        migrations.AlterField(
            model_name='vehicle',
            name='name',
            field=models.CharField(max_length=64, verbose_name='Name'),
        ),
        migrations.AlterUniqueTogether(
            name='vehicle',
            unique_together={('imei', 'owner')},
        ),
    ]