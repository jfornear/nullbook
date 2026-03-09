from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("api/auth/", include("core.auth_urls")),
    path("api/", include("core.urls")),
    path("api/accounts/", include("accounts.urls")),
    path("api/transactions/", include("transactions.urls")),
    path("api/portfolio/", include("portfolio.urls")),
    path("api/taxes/", include("taxes.urls")),
    path("api/news/", include("news.urls")),
    path("api/imports/", include("imports.urls")),
    path("api/chat/", include("chat.urls")),
    path("api/integrations/", include("integrations.urls")),
    path("api/email-sync/", include("email_sync.urls")),
]

if settings.DEBUG:
    urlpatterns += [path("admin/", admin.site.urls)]

# Serve uploaded media files (receipts, etc.) — in production this is behind nginx
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
