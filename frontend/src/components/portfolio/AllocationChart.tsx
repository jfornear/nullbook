import { useQuery } from "@tanstack/react-query";
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip, Legend } from "recharts";
import { api } from "@/lib/api";
import type { AllocationEntry } from "@/types";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { formatCurrency } from "@/lib/utils";

const COLORS: Record<string, string> = {
  stock: "hsl(var(--primary))",
  etf: "hsl(220 70% 55%)",
  mutual_fund: "hsl(160 60% 45%)",
  bond: "hsl(35 80% 50%)",
  crypto: "hsl(280 60% 55%)",
  other: "hsl(var(--muted-foreground))",
};

function getColor(type: string) {
  return COLORS[type] || COLORS.other;
}

export function AllocationChart() {
  const { data, isLoading } = useQuery({
    queryKey: ["allocation"],
    queryFn: () => api.get<AllocationEntry[]>("/portfolio/holdings/allocation/"),
  });

  const chartData = (data || []).map((entry) => ({
    name: entry.security_type.replace(/_/g, " "),
    value: parseFloat(entry.total_cost_basis),
    count: entry.count,
    fill: getColor(entry.security_type),
  }));

  if (isLoading) {
    return <Skeleton className="h-[400px] w-full rounded-lg" />;
  }

  if (chartData.length === 0) {
    return (
      <Card>
        <CardContent className="flex h-[300px] items-center justify-center">
          <p className="text-muted-foreground">Add holdings to see allocation breakdown.</p>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Portfolio Allocation</CardTitle>
      </CardHeader>
      <CardContent>
        <ResponsiveContainer width="100%" height={300}>
          <PieChart>
            <Pie
              data={chartData}
              cx="50%"
              cy="50%"
              innerRadius={60}
              outerRadius={100}
              dataKey="value"
              nameKey="name"
              paddingAngle={2}
            >
              {chartData.map((entry, i) => (
                <Cell key={i} fill={entry.fill} />
              ))}
            </Pie>
            <Tooltip
              formatter={(value: number) => formatCurrency(value)}
              contentStyle={{
                backgroundColor: "hsl(var(--card))",
                border: "1px solid hsl(var(--border))",
                borderRadius: "var(--radius)",
              }}
            />
            <Legend />
          </PieChart>
        </ResponsiveContainer>

        <div className="mt-4 grid gap-2">
          {chartData.map((entry) => (
            <div key={entry.name} className="flex items-center justify-between text-sm">
              <div className="flex items-center gap-2">
                <div className="h-3 w-3 rounded-full" style={{ backgroundColor: entry.fill }} />
                <span className="capitalize">{entry.name}</span>
                <span className="text-muted-foreground">({entry.count})</span>
              </div>
              <span className="font-medium">{formatCurrency(entry.value)}</span>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}
