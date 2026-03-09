const API_BASE = import.meta.env.VITE_API_URL || "";

let csrfToken: string | null = null;

export function setCsrfToken(token: string) {
  csrfToken = token;
}

export function getCsrfToken(): string | null {
  return csrfToken;
}

async function fetchAPI<T>(endpoint: string, options?: RequestInit): Promise<T> {
  const url = `${API_BASE}/api${endpoint}`;

  const headers: Record<string, string> = {};

  // Only set Content-Type for non-FormData bodies
  if (!(options?.body instanceof FormData)) {
    headers["Content-Type"] = "application/json";
  }

  // Attach CSRF token on all requests — SessionAuthentication enforces it
  if (csrfToken) {
    headers["X-CSRFToken"] = csrfToken;
  }

  const res = await fetch(url, {
    credentials: "include",
    ...options,
    headers: {
      ...headers,
      ...options?.headers,
    },
  });

  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: res.statusText }));
    if (error.detail) {
      throw new Error(error.detail);
    }
    // DRF field validators return {"field": ["msg", ...], ...} — flatten into a single message
    const fieldMessages = Object.values(error)
      .flat()
      .filter((v): v is string => typeof v === "string");
    if (fieldMessages.length > 0) {
      throw new Error(fieldMessages.join(" "));
    }
    throw new Error(`API error: ${res.status}`);
  }

  if (res.status === 204) return {} as T;
  return res.json();
}

export const api = {
  get: <T>(endpoint: string) => fetchAPI<T>(endpoint),
  post: <T>(endpoint: string, data?: unknown) =>
    fetchAPI<T>(endpoint, {
      method: "POST",
      body: data !== undefined ? JSON.stringify(data) : JSON.stringify({}),
    }),
  put: <T>(endpoint: string, data: unknown) =>
    fetchAPI<T>(endpoint, { method: "PUT", body: JSON.stringify(data) }),
  patch: <T>(endpoint: string, data: unknown) =>
    fetchAPI<T>(endpoint, { method: "PATCH", body: JSON.stringify(data) }),
  delete: <T>(endpoint: string) => fetchAPI<T>(endpoint, { method: "DELETE" }),
  upload: <T>(endpoint: string, formData: FormData) =>
    fetchAPI<T>(endpoint, {
      method: "POST",
      body: formData,
    }),
};

// --- Plaid integration helpers ---

export interface PlaidLinkToken {
  link_token: string;
  expiration: string;
  request_id: string;
}

export interface PlaidExchangeResult {
  item: {
    id: number;
    institution_name: string;
    status: string;
    last_synced_at: string | null;
  };
  accounts_synced?: number;
  already_connected: boolean;
}

export interface PlaidItem {
  id: number;
  item_id: string;
  institution_id: string;
  institution_name: string;
  status: string;
  error_code: string | null;
  error_message: string | null;
  last_synced_at: string | null;
  created_at: string;
}

export const plaidApi = {
  createLinkToken: () => api.post<PlaidLinkToken>("/integrations/plaid/link-token/"),
  exchangePublicToken: (publicToken: string, institutionId?: string, institutionName?: string) =>
    api.post<PlaidExchangeResult>("/integrations/plaid/exchange/", {
      public_token: publicToken,
      institution_id: institutionId,
      institution_name: institutionName,
    }),
  listItems: () => api.get<PlaidItem[]>("/integrations/plaid/items/"),
  syncItem: (plaidItemId: number) =>
    api.post<{ status: string }>("/integrations/plaid/sync/", { plaid_item_id: plaidItemId }),
  deleteItem: (plaidItemId: number) =>
    api.delete<{ status: string }>(`/integrations/plaid/items/${plaidItemId}/`),
};

// --- Email sync helpers ---

export interface EmailConnectResult {
  id?: number;
  status?: string;
}

export const emailApi = {
  connectImap: (data: {
    email_address: string;
    imap_host: string;
    imap_port: number;
    username: string;
    password: string;
  }) => api.post<EmailConnectResult>("/email-sync/accounts/connect-imap/", data),
  syncNow: (accountId: number) =>
    api.post<{ status: string }>(`/email-sync/accounts/${accountId}/sync-now/`),
  disconnect: (accountId: number) => api.delete(`/email-sync/accounts/${accountId}/`),
};
