from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion

class Migration(migrations.Migration):
    dependencies = [migrations.swappable_dependency(settings.AUTH_USER_MODEL), ("sentinel", "0001_initial")]
    operations = [migrations.AddField(model_name="event", name="owner", field=models.ForeignKey(blank=True, null=True, db_index=True, on_delete=django.db.models.deletion.PROTECT, related_name="sentinel_events", to=settings.AUTH_USER_MODEL))]
