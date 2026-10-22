from django.urls import path
from sentinel import views
urlpatterns = [
    path('healthz', views.health, name='health'),
    path('', views.home, name='home'),
    path('api/status', views.status, name='status'),
    path('api/dashboard', views.dashboard, name='dashboard'),
    path('api/events', views.events, name='events'),
    path('api/events/<int:pk>', views.event_detail, name='event_detail'),
    path('api/alerts', views.alerts, name='alerts'),
    path('api/alerts/<int:pk>', views.alert_detail, name='alert_detail'),
    path('api/alerts/<int:pk>/review', views.review_alert, name='review_alert'),
    path('api/rules', views.rules, name='rules'),
    path('api/rules/<int:pk>/toggle', views.toggle_rule, name='toggle_rule'),
    path('api/monitor/start', views.start_monitor, name='start_monitor'),
    path('api/monitor/stop', views.stop_monitor, name='stop_monitor'),
    path('api/demo/event', views.demo_event, name='demo_event'),
    path('api/demo/seed', views.seed_demo, name='seed_demo'),
    path('api/demo/date', views.seed_date, name='seed_date'),
    path('api/scenarios', views.scenarios, name='scenarios'),
    path('api/email/analyze', views.analyze_email_sample, name='email_analyze'),
]
