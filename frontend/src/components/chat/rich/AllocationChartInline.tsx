import { PieChart, Pie, Cell, Tooltip, ResponsiveContainer } from "recharts";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

interface AllocationData {
  allocation: {
    security_type: string;
    count: number;
    total_shares: string;
    total_cost_basis: string;
  }[];
}

const COLORS = [
  "hsl(var(--primary))",
  "hsl(var(--chart-2, 210 70% 50%))",
  "hsl(var(--chart-3, 150 60% 45%))",
  "hsl(var(--chart-4, 40 80% 55%))",
  "hsl(var(--chart-5, 0 70% 55%))",
];

export function AllocationChartInline({ data }: { data: unknown }) {
  const { allocation } = data as AllocationData;

  const chartData = allocation.map((a) => ({
    name: a.security_type,
    value: parseFloat(a.total_cost_basis),
  }));

  if (!chartData.length) {
    return (
      <Card>
        <CardContent className="py-4 text-center text-sm text-muted-foreground">
          No holdings data.
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="text-sm">Portfolio Allocation</CardTitle>
      </CardHeader>
      <CardContent>
        <ResponsiveContainer width="100%" height={200}>
          <PieChart>
            <Pie
              data={chartData}
              cx="50%"
              cy="50%"
              outerRadius={80}
              dataKey="value"
              label={({ name }) => name}
            >
              {chartData.map((_entry, index) => (
                <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
              ))}
            </Pie>
            <Tooltip
              contentStyle={{
                backgroundColor: "hsl(var(--card))",
                border: "1px solid hsl(var(--border))",
                borderRadius: "var(--radius)",
                fontSize: 12,
              }}
            />
          </PieChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  );
}
