"""The three core entities match the Python Sentinel SRS 3.2–3.8."""
from django.db import models

class Event(models.Model):
    event_id = models.AutoField(primary_key=True)
    event_time = models.DateTimeField(db_index=True)
    source = models.CharField(max_length=100)
    event_type = models.CharField(max_length=100)
    username = models.CharField(max_length=100, null=True, blank=True)
    message = models.TextField()
    severity = models.CharField(max_length=20, null=True, blank=True)
    class Meta:
        db_table = 'events'
        ordering = ['-event_id']

class DetectionRule(models.Model):
    rule_id = models.AutoField(primary_key=True)
    rule_name = models.CharField(max_length=100)
    description = models.TextField()
    pattern = models.CharField(max_length=255)
    severity = models.CharField(max_length=20)
    enabled = models.BooleanField(default=True)
    class Meta:
        db_table = 'detection_rules'
        ordering = ['rule_id']

class Alert(models.Model):
    alert_id = models.AutoField(primary_key=True)
    event = models.ForeignKey(Event, on_delete=models.PROTECT, db_column='event_id', related_name='alerts')
    rule = models.ForeignKey(DetectionRule, on_delete=models.PROTECT, db_column='rule_id', related_name='alerts')
    alert_time = models.DateTimeField(db_index=True)
    severity = models.CharField(max_length=20)
    description = models.TextField()
    status = models.CharField(max_length=20, default='Open')
    class Meta:
        db_table = 'alerts'
        ordering = ['-alert_id']
