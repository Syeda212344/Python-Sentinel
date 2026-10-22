from django.db import migrations, models
import django.db.models.deletion

class Migration(migrations.Migration):
    initial = True
    dependencies = []
    operations = [
        migrations.CreateModel(name='Event', fields=[
            ('event_id', models.AutoField(primary_key=True, serialize=False)),
            ('event_time', models.DateTimeField(db_index=True)),
            ('source', models.CharField(max_length=100)),
            ('event_type', models.CharField(max_length=100)),
            ('username', models.CharField(max_length=100, blank=True, null=True)),
            ('message', models.TextField()),
            ('severity', models.CharField(max_length=20, blank=True, null=True)),
        ], options={'db_table':'events','ordering':['-event_id']}),
        migrations.CreateModel(name='DetectionRule', fields=[
            ('rule_id', models.AutoField(primary_key=True, serialize=False)),
            ('rule_name', models.CharField(max_length=100)),
            ('description', models.TextField()),
            ('pattern', models.CharField(max_length=255)),
            ('severity', models.CharField(max_length=20)),
            ('enabled', models.BooleanField(default=True)),
        ], options={'db_table':'detection_rules','ordering':['rule_id']}),
        migrations.CreateModel(name='Alert', fields=[
            ('alert_id', models.AutoField(primary_key=True, serialize=False)),
            ('alert_time', models.DateTimeField(db_index=True)),
            ('severity', models.CharField(max_length=20)),
            ('description', models.TextField()),
            ('status', models.CharField(max_length=20, default='Open')),
            ('event', models.ForeignKey(db_column='event_id', on_delete=django.db.models.deletion.PROTECT, related_name='alerts', to='sentinel.event')),
            ('rule', models.ForeignKey(db_column='rule_id', on_delete=django.db.models.deletion.PROTECT, related_name='alerts', to='sentinel.detectionrule')),
        ], options={'db_table':'alerts','ordering':['-alert_id']}),
    ]
