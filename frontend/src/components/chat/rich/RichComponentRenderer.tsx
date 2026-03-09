import { Component, type ReactNode } from "react";
import { AccountsTable } from "./AccountsTable";
import { TransactionsTable } from "./TransactionsTable";
import { SpendingChartInline } from "./SpendingChartInline";
import { PortfolioHoldingsTable } from "./PortfolioHoldingsTable";
import { AllocationChartInline } from "./AllocationChartInline";
import { DashboardSummaryCard } from "./DashboardSummaryCard";
import { NewsArticleCards } from "./NewsArticleCards";
import { SecurityLookupCard } from "./SecurityLookupCard";
import { TaxYearsSummary } from "./TaxYearsSummary";
import { ReceiptCard } from "./ReceiptCard";
import { ReceiptsList } from "./ReceiptsList";
import { ExpenseReport } from "./ExpenseReport";
import { TaxEstimateCard } from "./TaxEstimateCard";
import { FilingComparison } from "./FilingComparison";
import { DeductionSuggestions } from "./DeductionSuggestions";
import { TaxChecklist } from "./TaxChecklist";
import { SubscriptionsTable } from "./SubscriptionsTable";
import { AlertsList } from "./AlertsList";
import { TaxSummaryExport } from "./TaxSummaryExport";
import { ScheduleCCard } from "./ScheduleCCard";
import { PortfolioPerformance } from "./PortfolioPerformance";
import { CancellationDraft } from "./CancellationDraft";
import { TaxFilingPrep } from "./TaxFilingPrep";
import { SyncStatus } from "./SyncStatus";
import { WeeklySummary } from "./WeeklySummary";

class RichComponentErrorBoundary extends Component<{ children: ReactNode }, { hasError: boolean }> {
  constructor(props: { children: ReactNode }) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError(): { hasError: boolean } {
    return { hasError: true };
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="rounded-md border border-destructive/50 bg-destructive/10 p-3 text-sm text-muted-foreground">
          Failed to display this content.
        </div>
      );
    }
    return this.props.children;
  }
}

export interface RichComponentData {
  component_type: string;
  [key: string]: unknown;
}

interface RichComponentRendererProps {
  data: RichComponentData | unknown;
}

const componentMap: Record<string, React.ComponentType<{ data: unknown }>> = {
  accounts_table: AccountsTable as React.ComponentType<{ data: unknown }>,
  transactions_table: TransactionsTable as React.ComponentType<{ data: unknown }>,
  spending_chart: SpendingChartInline as React.ComponentType<{ data: unknown }>,
  portfolio_holdings: PortfolioHoldingsTable as React.ComponentType<{ data: unknown }>,
  allocation_chart: AllocationChartInline as React.ComponentType<{ data: unknown }>,
  dashboard_summary: DashboardSummaryCard as React.ComponentType<{ data: unknown }>,
  news_articles: NewsArticleCards as React.ComponentType<{ data: unknown }>,
  security_lookup: SecurityLookupCard as React.ComponentType<{ data: unknown }>,
  tax_years: TaxYearsSummary as React.ComponentType<{ data: unknown }>,
  // Phase 1: Receipt & Expense
  receipt_card: ReceiptCard as React.ComponentType<{ data: unknown }>,
  receipts_list: ReceiptsList as React.ComponentType<{ data: unknown }>,
  expense_report: ExpenseReport as React.ComponentType<{ data: unknown }>,
  // Phase 2: Tax Estimation
  tax_estimate: TaxEstimateCard as React.ComponentType<{ data: unknown }>,
  filing_comparison: FilingComparison as React.ComponentType<{ data: unknown }>,
  // Phase 3: Tax Prep
  deduction_suggestions: DeductionSuggestions as React.ComponentType<{ data: unknown }>,
  tax_checklist: TaxChecklist as React.ComponentType<{ data: unknown }>,
  // Phase 4: Subscriptions, Alerts, Portfolio, Cancellation, Tax Filing
  subscriptions_table: SubscriptionsTable as React.ComponentType<{ data: unknown }>,
  subscription_spending: SubscriptionsTable as React.ComponentType<{ data: unknown }>,
  alerts_list: AlertsList as React.ComponentType<{ data: unknown }>,
  tax_summary_export: TaxSummaryExport as React.ComponentType<{ data: unknown }>,
  tax_csv_export: TaxSummaryExport as React.ComponentType<{ data: unknown }>,
  schedule_c: ScheduleCCard as React.ComponentType<{ data: unknown }>,
  portfolio_performance: PortfolioPerformance as React.ComponentType<{ data: unknown }>,
  cancellation_draft: CancellationDraft as React.ComponentType<{ data: unknown }>,
  cancellation_sent: CancellationDraft as React.ComponentType<{ data: unknown }>,
  cancellation_manual: CancellationDraft as React.ComponentType<{ data: unknown }>,
  cancellation_tracking: CancellationDraft as React.ComponentType<{ data: unknown }>,
  tax_filing_prep: TaxFilingPrep as React.ComponentType<{ data: unknown }>,
  sync_status: SyncStatus as React.ComponentType<{ data: unknown }>,
  email_connect: SyncStatus as React.ComponentType<{ data: unknown }>,
  plaid_link: SyncStatus as React.ComponentType<{ data: unknown }>,
  missed_deductions: DeductionSuggestions as React.ComponentType<{ data: unknown }>,
  email_receipts: ReceiptsList as React.ComponentType<{ data: unknown }>,
  weekly_summary: WeeklySummary as React.ComponentType<{ data: unknown }>,
};

export function RichComponentRenderer({ data }: RichComponentRendererProps) {
  const d = data as RichComponentData | null | undefined;
  if (!d?.component_type) return null;

  const Comp = componentMap[d.component_type];
  if (!Comp) return null;

  return (
    <div className="my-2 w-full">
      <RichComponentErrorBoundary>
        <Comp data={d} />
      </RichComponentErrorBoundary>
    </div>
  );
}
