from django.db import migrations

def create_vehicle_types(apps, schema_editor):
    VehicleType = apps.get_model('vehicles', 'VehicleType')
    choices = [
        "Two Wheeler",
        "Three Wheeler",
        "Four Wheeler",
    ]
    for name in choices:
        VehicleType.objects.get_or_create(name=name)

class Migration(migrations.Migration):
    dependencies = [
        ('vehicles', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(create_vehicle_types),
    ]