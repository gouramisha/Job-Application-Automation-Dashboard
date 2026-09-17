from django.urls import path

from . import views

urlpatterns = [
    path("dashboard/", views.dashboard, name="analytics-dashboard"),
    path("summary/", views.summary, name="analytics-summary"),
    path("timeline/", views.timeline, name="analytics-timeline"),
    path("status-timeline/", views.status_timeline, name="analytics-status-timeline"),
    path("breakdowns/", views.breakdowns, name="analytics-breakdowns"),
    path("funnel/", views.funnel, name="analytics-funnel"),
]
