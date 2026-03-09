export interface Account {
  id: number;
  institution: number | null;
  institution_name: string;
  institution_logo_url: string;
  name: string;
  account_type: string;
  balance: string;
  currency: string;
  is_active: boolean;
  notes: string;
  created_at: string;
  updated_at: string;
}

export interface Institution {
  id: number;
  name: string;
  institution_type: string;
  website: string;
  logo_url: string;
}

export interface Category {
  id: number;
  name: string;
  parent: number | null;
  icon: string;
  children?: Category[];
}

export interface Tag {
  id: number;
  name: string;
  color: string;
}

export interface Transaction {
  id: number;
  account: number;
  category: number | null;
  category_name: string;
  tags: number[];
  date: string;
  amount: string;
  transaction_type: "income" | "expense" | "transfer";
  description: string;
  notes: string;
  is_recurring: boolean;
  created_at: string;
  updated_at: string;
}

export interface Security {
  id: number;
  symbol: string;
  name: string;
  security_type: string;
  exchange: string;
  currency: string;
}

export interface SecurityLookup extends Security {
  current_price: string | null;
}

export interface Holding {
  id: number;
  account: number | null;
  account_name: string | null;
  security: number;
  security_symbol: string;
  security_name: string;
  shares: string;
  cost_basis: string;
}

export interface DashboardSummary {
  total_accounts: number;
  net_worth: string;
  recent_transactions: number;
  portfolio_value: string;
}

export interface SpendingSummary {
  category_id: number;
  category_name: string;
  total: string;
}

export interface ImportBatch {
  id: number;
  account: number;
  file_name: string;
  status: string;
  row_count: number;
  imported_count: number;
  error_log: string;
  created_at: string;
}

export interface TaxYear {
  id: number;
  year: number;
  filing_status: string;
  documents?: TaxDocument[];
  deductions?: DeductibleExpense[];
  created_at: string;
  updated_at: string;
}

export interface TaxDocument {
  id: number;
  tax_year: number;
  document_type: string;
  issuer: string;
  amount: string;
  notes: string;
  created_at: string;
}

export interface DeductibleExpense {
  id: number;
  tax_year: number;
  deduction_type: string;
  description: string;
  amount: string;
  is_verified: boolean;
  created_at: string;
}

export interface NewsSource {
  id: number;
  name: string;
  url: string;
  feed_url: string;
  is_active: boolean;
  created_at: string;
}

export interface NewsArticle {
  id: number;
  source: number;
  source_name: string;
  title: string;
  url: string;
  summary: string;
  published_at: string;
  is_read: boolean;
  is_bookmarked: boolean;
}

export interface Watchlist {
  id: number;
  name: string;
  keywords: string;
  created_at: string;
}

export interface UserSettings {
  id: number;
  user: number;
  currency: string;
  fiscal_year_start: number;
  created_at: string;
  updated_at: string;
}

export interface UploadPreview {
  batch_id: number;
  file_name: string;
  headers: string[];
  preview: Record<string, string>[];
  detected_mapping: Record<string, string>;
  row_count: number;
  rows?: Record<string, string>[];
}

export interface ImportExecuteResult {
  batch_id: number;
  status: string;
  imported_count: number;
  error_count: number;
  errors: string[];
}

export interface PaginatedResponse<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}

export interface AllocationEntry {
  security_type: string;
  count: number;
  total_shares: number;
  total_cost_basis: string;
}

export interface Goal {
  id: number;
  name: string;
  target_amount: string;
  current_amount: string;
  target_date: string | null;
  category: number | null;
  category_name: string | null;
  linked_account: number | null;
  account_name: string | null;
  progress_pct: number;
  created_at: string;
  updated_at: string;
}

export interface Budget {
  id: number;
  category: number | null;
  category_name: string;
  amount: string;
  period: "weekly" | "monthly" | "annual";
  is_active: boolean;
  spent: string;
  created_at: string;
  updated_at: string;
}

export interface CategoryRule {
  id: number;
  pattern: string;
  category: number;
  category_name: string;
  created_at: string;
}
