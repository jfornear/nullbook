from django.urls import path

from . import views

urlpatterns = [
    path("health/", views.health_check, name="health-check"),
    path("auth/change-password/", views.change_password_view, name="change-password"),
    path("dashboard/", views.DashboardSummaryView.as_view(), name="dashboard-summary"),
    path("settings/", views.UserSettingsView.as_view(), name="user-settings"),
    path("integrations/status/", views.IntegrationStatusView.as_view(), name="integration-status"),
    path("insights/", views.InsightsView.as_view(), name="insights"),
    path("net-worth-history/", views.NetWorthHistoryView.as_view(), name="net-worth-history"),
    path("alerts/", views.AlertListView.as_view(), name="alerts-list"),
    path("alerts/mark-read/", views.mark_alerts_read, name="alerts-mark-read"),
    path("alerts/delete/", views.delete_alerts, name="alerts-delete"),
]
