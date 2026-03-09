import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from "recharts";
import { format, subDays, startOfYear } from "date-fns";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { api } from "@/lib/api";
import type { SpendingSummary } from "@/types";
import { DateRangePicker } from "@/components/shared/DateRangePicker";

type Period = "30d" | "90d" | "year" | "custom";

function getDateRange(period: Period): { from?: string; to?: string } {
  const today = new Date();
  const fmt = (d: Date) => format(d, "yyyy-MM-dd");
  switch (period) {
    case "30d":
      return { from: fmt(subDays(today, 30)), to: fmt(today) };
    case "90d":
      return { from: fmt(subDays(today, 90)), to: fmt(today) };
    case "year":
      return { from: fmt(startOfYear(today)), to: fmt(today) };
    default:
      return {};
  }
}

export function SpendingChart() {
  const [period, setPeriod] = useState<Period>("30d");
  const [customRange, setCustomRange] = useState<{ from?: string; to?: string }>({});

  const dateRange = period === "custom" ? customRange : getDateRange(period);

  const params = new URLSearchParams();
  if (dateRange.from) params.set("date_from", dateRange.from);
  if (dateRange.to) params.set("date_to", dateRange.to);
  const qs = params.toString();

  const { data } = useQuery({
    queryKey: ["spending-summary", dateRange],
    queryFn: () =>
      api.get<SpendingSummary[]>(
        `/transactions/transactions/spending_summary/${qs ? `?${qs}` : ""}`
      ),
  });

  const chartData = (data || []).map((item) => ({
    name: item.category_name,
    amount: parseFloat(item.total),
  }));

  return (
    <Card className="col-span-full">
      <CardHeader>
        <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <CardTitle>Spending by Category</CardTitle>
          <div className="flex flex-wrap items-center gap-2">
            {(
              [
                { value: "30d", label: "30 days" },
                { value: "90d", label: "90 days" },
                { value: "year", label: "This year" },
              ] as { value: Period; label: string }[]
            ).map((opt) => (
              <Button
                key={opt.value}
                variant={period === opt.value ? "default" : "outline"}
                size="sm"
                className="h-7 text-xs"
                onClick={() => setPeriod(opt.value)}
              >
                {opt.label}
              </Button>
            ))}
            <DateRangePicker
              from={period === "custom" ? customRange.from : undefined}
              to={period === "custom" ? customRange.to : undefined}
              onChange={(range) => {
                setCustomRange(range);
                setPeriod("custom");
              }}
            />
          </div>
        </div>
      </CardHeader>
      <CardContent>
        {chartData.length > 0 ? (
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
              <XAxis
                dataKey="name"
                className="text-xs"
                tick={{ fill: "hsl(var(--muted-foreground))" }}
              />
              <YAxis className="text-xs" tick={{ fill: "hsl(var(--muted-foreground))" }} />
              <Tooltip
                contentStyle={{
                  backgroundColor: "hsl(var(--card))",
                  border: "1px solid hsl(var(--border))",
                  borderRadius: "var(--radius)",
                }}
              />
              <Bar dataKey="amount" fill="hsl(var(--primary))" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        ) : (
          <div className="flex h-[300px] items-center justify-center text-muted-foreground">
            No spending data yet. Import or add transactions to see your spending breakdown.
          </div>
        )}
      </CardContent>
    </Card>
  );
}
