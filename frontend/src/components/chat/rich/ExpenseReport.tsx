import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { FileText } from "lucide-react";
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from "recharts";

interface ExpenseCategory {
  category: string;
  total: string;
  count: number;
  items: { id: number; description: string; amount: string; is_verified: boolean }[];
}

interface ExpenseReportData {
  tax_year: number;
  filing_status: string;
  categories: ExpenseCategory[];
  grand_total: string;
}

const COLORS = [
  "#6366f1",
  "#8b5cf6",
  "#a855f7",
  "#ec4899",
  "#f43f5e",
  "#f97316",
  "#eab308",
  "#22c55e",
  "#14b8a6",
  "#06b6d4",
];

export function ExpenseReport({ data }: { data: unknown }) {
  const d = data as ExpenseReportData;

  const chartData = d.categories.map((c) => ({
    name: c.category,
    amount: parseFloat(c.total),
  }));

  return (
    <Card>
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between">
          <CardTitle className="flex items-center gap-2 text-sm">
            <FileText className="h-4 w-4" />
            {d.tax_year} Expense Report
          </CardTitle>
          <span className="text-sm font-semibold">
            Total: $
            {parseFloat(d.grand_total).toLocaleString("en-US", { minimumFractionDigits: 2 })}
          </span>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        {chartData.length > 0 && (
          <div className="h-40">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={chartData} layout="vertical" margin={{ left: 10, right: 10 }}>
                <XAxis
                  type="number"
                  tickFormatter={(v) => `$${v.toLocaleString()}`}
                  className="text-[10px]"
                />
                <YAxis type="category" dataKey="name" width={120} className="text-[10px]" />
                <Tooltip
                  formatter={(v: number) =>
                    `$${v.toLocaleString("en-US", { minimumFractionDigits: 2 })}`
                  }
                />
                <Bar dataKey="amount" radius={[0, 4, 4, 0]}>
                  {chartData.map((_, i) => (
                    <Cell key={i} fill={COLORS[i % COLORS.length]} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        )}

        <div className="space-y-1">
          {d.categories.map((cat) => (
            <div key={cat.category} className="rounded-md border px-3 py-2">
              <div className="flex items-center justify-between text-sm">
                <span className="font-medium">{cat.category}</span>
                <span className="font-semibold">
                  ${parseFloat(cat.total).toLocaleString("en-US", { minimumFractionDigits: 2 })}
                </span>
              </div>
              <div className="text-xs text-muted-foreground">
                {cat.count} expense{cat.count !== 1 ? "s" : ""}
              </div>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}
