import { useNavigate } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { useCreateConversation } from "@/lib/chat";
import { useSession } from "@/lib/auth";
import { ChatInput } from "./ChatInput";
import { api } from "@/lib/api";
import type { DashboardSummary, NewsArticle, PaginatedResponse } from "@/types";
import { formatCurrency } from "@/lib/utils";

interface HoldingPerformance {
  id: number;
  symbol: string;
  name: string;
  shares: string;
  current_price: string | null;
  market_value: string;
  unrealized_gain: string;
  unrealized_gain_pct: number;
  day_change: string;
  day_change_pct: number;
}

interface PerformanceData {
  total_market_value: string;
  total_cost_basis: string;
  total_unrealized_gain: string;
  total_unrealized_gain_pct: number;
  day_change: string;
  day_change_pct: number;
  holdings: HoldingPerformance[];
}

const suggestions = [
  "What's my net worth?",
  "Show my portfolio",
  "Recent transactions",
  "Analyze my spending",
];

function getGreeting(): string {
  const hour = new Date().getHours();
  if (hour < 12) return "Good morning";
  if (hour < 17) return "Good afternoon";
  return "Good evening";
}

export function HomeView() {
  const navigate = useNavigate();
  const createConversation = useCreateConversation();
  const { data: user } = useSession();

  const { data: dashboard } = useQuery({
    queryKey: ["dashboard"],
    queryFn: () => api.get<DashboardSummary>("/dashboard/"),
  });

  const hasInvestments = dashboard && parseFloat(dashboard.portfolio_value) > 0;

  const { data: articlesData } = useQuery({
    queryKey: ["articles"],
    queryFn: () => api.get<PaginatedResponse<NewsArticle>>("/news/articles/"),
    enabled: !!hasInvestments,
  });

  const { data: perfData } = useQuery({
    queryKey: ["portfolio-performance"],
    queryFn: () => api.get<PerformanceData>("/portfolio/holdings/performance/"),
    enabled: !!hasInvestments,
  });

  async function handleSend(content: string) {
    try {
      const convo = await createConversation.mutateAsync({ title: "" });
      navigate(`/c/${convo.id}`, { state: { initialMessage: content } });
    } catch {
      // toast handled by mutation
    }
  }

  const isSending = createConversation.isPending;

  // Show top holdings — use day change if most holdings moved, otherwise unrealized gain
  const allHoldings = perfData?.holdings ?? [];
  const movingCount = allHoldings.filter((h) => h.day_change_pct !== 0).length;
  const marketOpen = movingCount > allHoldings.length / 2;
  const topMovers = [...allHoldings]
    .sort((a, b) =>
      marketOpen
        ? Math.abs(b.day_change_pct) - Math.abs(a.day_change_pct)
        : Math.abs(b.unrealized_gain_pct) - Math.abs(a.unrealized_gain_pct)
    )
    .slice(0, 5);
  const latestNews = (articlesData?.results ?? []).slice(0, 8);

  return (
    <div className="flex h-full flex-col items-center px-4 py-6 overflow-y-auto">
      <div className="w-full max-w-3xl flex-1 flex flex-col justify-center space-y-6">
        <div className="text-center">
          <h1 className="text-3xl font-semibold tracking-tight">
            {getGreeting()}
            {user ? `, ${user.username}` : ""}
          </h1>
        </div>

        <ChatInput onSend={handleSend} disabled={isSending} autoFocus />

        <div className="flex flex-wrap items-center justify-center gap-2">
          {suggestions.map((s) => (
            <button
              key={s}
              onClick={() => handleSend(s)}
              disabled={isSending}
              className="rounded-full border px-3 py-1.5 text-xs text-muted-foreground transition-colors hover:bg-accent hover:text-accent-foreground disabled:opacity-50"
            >
              {s}
            </button>
          ))}
        </div>

        {hasInvestments && topMovers.length > 0 && (
          <div className="-mx-4 px-4 overflow-x-auto scrollbar-none">
            <div className="flex items-stretch gap-2 w-max mx-auto">
              {topMovers.map((holding) => {
                const changeNum = marketOpen
                  ? parseFloat(holding.day_change)
                  : parseFloat(holding.unrealized_gain);
                const changePct = marketOpen ? holding.day_change_pct : holding.unrealized_gain_pct;
                const color =
                  changeNum > 0
                    ? "text-green-600"
                    : changeNum < 0
                      ? "text-red-600"
                      : "text-muted-foreground";
                const label = marketOpen ? "today" : "total";
                return (
                  <button
                    key={holding.id}
                    onClick={() =>
                      handleSend(
                        marketOpen
                          ? `Analyze ${holding.symbol} — it's ${changeNum > 0 ? "up" : "down"} ${Math.abs(changePct).toFixed(2)}% today`
                          : `Analyze my ${holding.symbol} position`
                      )
                    }
                    disabled={isSending}
                    className="w-36 shrink-0 rounded-lg border px-3 py-2.5 text-left hover:bg-accent/50 transition-colors disabled:opacity-50"
                  >
                    <div className="flex items-baseline justify-between mb-1">
                      <span className="text-xs font-medium">{holding.symbol}</span>
                      <span className="text-[10px] text-muted-foreground">
                        {holding.current_price
                          ? formatCurrency(holding.current_price)
                          : formatCurrency(holding.market_value)}
                      </span>
                    </div>
                    <div className={`text-sm font-semibold ${color}`}>
                      {changeNum > 0 ? "+" : ""}
                      {changePct.toFixed(2)}%
                    </div>
                    <div className={`text-[10px] ${color}`}>
                      {changeNum > 0 ? "+" : ""}
                      {formatCurrency(
                        marketOpen ? holding.day_change : holding.unrealized_gain
                      )}{" "}
                      {label}
                    </div>
                  </button>
                );
              })}
            </div>
          </div>
        )}

        {hasInvestments && latestNews.length > 0 && (
          <div className="space-y-2">
            <h3 className="text-xs font-medium uppercase tracking-wider text-muted-foreground px-3">
              Top News
            </h3>
            <div>
              {latestNews.map((article) => (
                <button
                  key={article.id}
                  onClick={() => handleSend(`Summarize this news story: "${article.title}"`)}
                  disabled={isSending}
                  className="w-full rounded-lg px-3 py-2.5 text-left hover:bg-accent/50 transition-colors disabled:opacity-50"
                >
                  <span className="text-sm font-medium leading-snug line-clamp-1 block">
                    {article.title}
                  </span>
                  <span className="text-xs text-muted-foreground mt-0.5 block">
                    {article.source_name}
                  </span>
                </button>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
