import logging

import plaid
from django.conf import settings
from plaid.api import plaid_api
from plaid.model.accounts_get_request import AccountsGetRequest
from plaid.model.country_code import CountryCode
from plaid.model.item_public_token_exchange_request import (
    ItemPublicTokenExchangeRequest,
)
from plaid.model.link_token_create_request import LinkTokenCreateRequest
from plaid.model.link_token_create_request_user import LinkTokenCreateRequestUser
from plaid.model.products import Products
from plaid.model.transactions_sync_request import TransactionsSyncRequest

logger = logging.getLogger(__name__)


PLAID_ENV_MAP = {
    "sandbox": plaid.Environment.Sandbox,
    "production": plaid.Environment.Production,
}


def get_plaid_client():
    """Create and return a configured Plaid API client."""
    env_str = getattr(settings, "PLAID_ENV", "sandbox")
    host = PLAID_ENV_MAP.get(env_str, plaid.Environment.Sandbox)
    configuration = plaid.Configuration(
        host=host,
        api_key={
            "clientId": settings.PLAID_CLIENT_ID,
            "secret": settings.PLAID_SECRET,
        },
    )
    api_client = plaid.ApiClient(configuration)
    return plaid_api.PlaidApi(api_client)


def create_link_token(user):
    """Create a Plaid Link token for initializing Plaid Link in the frontend.

    Args:
        user: Django User instance.

    Returns:
        dict with link_token, expiration, and request_id.
    """
    client = get_plaid_client()

    request = LinkTokenCreateRequest(
        user=LinkTokenCreateRequestUser(client_user_id=str(user.id)),
        client_name=getattr(settings, "PLAID_CLIENT_NAME", "nullbook"),
        products=[Products("transactions")],
        country_codes=[CountryCode("US")],
        language="en",
    )

    response = client.link_token_create(request)
    return {
        "link_token": response.link_token,
        "expiration": response.expiration,
        "request_id": response.request_id,
    }


def exchange_public_token(public_token):
    """Exchange a Plaid public token for an access token and item ID.

    Args:
        public_token: The public_token from Plaid Link.

    Returns:
        dict with access_token, item_id, and request_id.
    """
    client = get_plaid_client()

    request = ItemPublicTokenExchangeRequest(public_token=public_token)
    response = client.item_public_token_exchange(request)

    return {
        "access_token": response.access_token,
        "item_id": response.item_id,
        "request_id": response.request_id,
    }


def sync_transactions(access_token, cursor=None):
    """Fetch transaction updates using Plaid's transactions/sync endpoint.

    Args:
        access_token: Plaid access token.
        cursor: Optional sync cursor from previous call.

    Returns:
        dict with added, modified, removed transactions, next_cursor,
        and has_more flag.
    """
    client = get_plaid_client()

    request_kwargs = {"access_token": access_token}
    if cursor:
        request_kwargs["cursor"] = cursor

    request = TransactionsSyncRequest(**request_kwargs)
    response = client.transactions_sync(request)

    return {
        "added": response.added,
        "modified": response.modified,
        "removed": response.removed,
        "next_cursor": response.next_cursor,
        "has_more": response.has_more,
        "accounts": response.accounts,
        "request_id": response.request_id,
    }


def get_accounts(access_token):
    """Retrieve accounts associated with a Plaid access token.

    Args:
        access_token: Plaid access token.

    Returns:
        dict with accounts list and request_id.
    """
    client = get_plaid_client()

    request = AccountsGetRequest(access_token=access_token)
    response = client.accounts_get(request)

    return {
        "accounts": response.accounts,
        "request_id": response.request_id,
    }
