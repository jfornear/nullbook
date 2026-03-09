from django.urls import path

from . import views

app_name = "integrations"

urlpatterns = [
    path("plaid/link-token/", views.create_link_token_view, name="plaid-link-token"),
    path("plaid/exchange/", views.exchange_token_view, name="plaid-exchange"),
    path("plaid/sync/", views.sync_item_view, name="plaid-sync"),
    path("plaid/items/", views.list_plaid_items_view, name="plaid-items"),
    path("plaid/items/<int:pk>/", views.delete_plaid_item_view, name="plaid-item-delete"),
]
