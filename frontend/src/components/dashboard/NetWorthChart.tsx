import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { api } from "@/lib/api";
import { formatCurrency } from "@/lib/utils";

type Period = "30d" | "90d" | "1y" | "all";

interface NetWorthEntry {
  date: string;
  net_worth: string;
}

export function NetWorthChart() {
  const [period, setPeriod] = useState<Period>("90d");

  const { data } = useQuery({
    queryKey: ["net-worth-history", period],
    queryFn: () => api.get<NetWorthEntry[]>(`/net-worth-history/?period=${period}`),
  });

  const chartData = (data || []).map((entry) => ({
    date: entry.date,
    value: parseFloat(entry.net_worth),
  }));

  return (
    <Card>
      <CardHeader>
        <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <CardTitle>Net Worth Over Time</CardTitle>
          <div className="flex gap-1">
            {(
              [
                { value: "30d", label: "30d" },
                { value: "90d", label: "90d" },
                { value: "1y", label: "1y" },
                { value: "all", label: "All" },
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
          </div>
        </div>
      </CardHeader>
      <CardContent>
        {chartData.length > 0 ? (
          <ResponsiveContainer width="100%" height={250}>
            <AreaChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
              <XAxis
                dataKey="date"
                className="text-xs"
                tick={{ fill: "hsl(var(--muted-foreground))" }}
                tickFormatter={(v) => {
                  const d = new Date(v);
                  return `${d.getMonth() + 1}/${d.getDate()}`;
                }}
              />
              <YAxis
                className="text-xs"
                tick={{ fill: "hsl(var(--muted-foreground))" }}
                tickFormatter={(v) => `$${(v / 1000).toFixed(0)}k`}
              />
              <Tooltip
                contentStyle={{
                  backgroundColor: "hsl(var(--card))",
                  border: "1px solid hsl(var(--border))",
                  borderRadius: "var(--radius)",
                }}
                formatter={(value: number) => [formatCurrency(value), "Net Worth"]}
                labelFormatter={(label) => new Date(label).toLocaleDateString()}
              />
              <Area
                type="monotone"
                dataKey="value"
                stroke="hsl(var(--primary))"
                fill="hsl(var(--primary))"
                fillOpacity={0.1}
                strokeWidth={2}
              />
            </AreaChart>
          </ResponsiveContainer>
        ) : (
          <div className="flex h-[250px] items-center justify-center text-sm text-muted-foreground">
            No balance history yet. Add accounts with balance snapshots to see trends.
          </div>
        )}
      </CardContent>
    </Card>
  );
}
