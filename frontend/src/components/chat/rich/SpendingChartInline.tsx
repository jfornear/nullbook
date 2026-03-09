import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from "recharts";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

interface SpendingData {
  categories: { category_name: string; total: string }[];
}

export function SpendingChartInline({ data }: { data: unknown }) {
  const { categories } = data as SpendingData;
  const chartData = categories.map((c) => ({
    name: c.category_name,
    amount: parseFloat(c.total),
  }));

  if (!chartData.length) {
    return (
      <Card>
        <CardContent className="py-4 text-center text-sm text-muted-foreground">
          No spending data for this period.
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="text-sm">Spending by Category</CardTitle>
      </CardHeader>
      <CardContent>
        <ResponsiveContainer width="100%" height={200}>
          <BarChart data={chartData}>
            <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
            <XAxis dataKey="name" tick={{ fill: "hsl(var(--muted-foreground))", fontSize: 10 }} />
            <YAxis tick={{ fill: "hsl(var(--muted-foreground))", fontSize: 10 }} />
            <Tooltip
              contentStyle={{
                backgroundColor: "hsl(var(--card))",
                border: "1px solid hsl(var(--border))",
                borderRadius: "var(--radius)",
                fontSize: 12,
              }}
            />
            <Bar dataKey="amount" fill="hsl(var(--primary))" radius={[4, 4, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  );
}
