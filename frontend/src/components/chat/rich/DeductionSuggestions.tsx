import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Search, Plus } from "lucide-react";
import { useChatAction } from "../ChatActionContext";

interface SuggestionTransaction {
  id: number;
  date: string;
  description: string;
  amount: string;
  category_name: string;
}

interface Suggestion {
  deduction_type: string;
  deduction_type_display: string;
  transaction_count: number;
  total_amount: string;
  existing_claimed: string;
  unclaimed_amount: string;
  transactions: SuggestionTransaction[];
}

interface DeductionSuggestionsData {
  tax_year: number;
  suggestions: Suggestion[];
  total_unclaimed: string;
}

export function DeductionSuggestions({ data }: { data: unknown }) {
  const d = data as DeductionSuggestionsData;
  const chatAction = useChatAction();

  if (!d.suggestions || d.suggestions.length === 0) {
    return (
      <Card>
        <CardContent className="py-4 text-center text-sm text-muted-foreground">
          No unclaimed deductions found in your transactions.
        </CardContent>
      </Card>
    );
  }

  const fmt = (v: string) =>
    "$" + parseFloat(v).toLocaleString("en-US", { minimumFractionDigits: 2 });

  function handleAdd(suggestion: Suggestion) {
    if (!chatAction) return;
    const ids = suggestion.transactions.map((t) => t.id).join(",");
    chatAction.sendMessage(
      `Create a ${suggestion.deduction_type} deduction from transactions ${ids} for ${d.tax_year}`
    );
  }

  return (
    <Card>
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between">
          <CardTitle className="flex items-center gap-2 text-sm">
            <Search className="h-4 w-4" />
            Potential Deductions Found
          </CardTitle>
          <Badge variant="secondary" className="text-xs">
            {fmt(d.total_unclaimed)} unclaimed
          </Badge>
        </div>
      </CardHeader>
      <CardContent className="space-y-3">
        {d.suggestions.map((s) => (
          <div key={s.deduction_type} className="rounded-md border p-3">
            <div className="flex items-center justify-between mb-2">
              <div>
                <span className="text-sm font-medium">{s.deduction_type_display}</span>
                <div className="text-xs text-muted-foreground">
                  {s.transaction_count} transactions · {fmt(s.unclaimed_amount)} unclaimed
                </div>
              </div>
              <Button
                size="sm"
                variant="outline"
                className="h-7 text-xs gap-1"
                onClick={() => handleAdd(s)}
              >
                <Plus className="h-3 w-3" /> Add
              </Button>
            </div>
            <div className="space-y-0.5">
              {s.transactions.slice(0, 5).map((t) => (
                <div key={t.id} className="flex justify-between text-xs text-muted-foreground">
                  <span className="truncate flex-1">
                    {t.date} — {t.description}
                  </span>
                  <span className="ml-2 font-medium text-foreground">{fmt(t.amount)}</span>
                </div>
              ))}
              {s.transactions.length > 5 && (
                <div className="text-xs text-muted-foreground italic">
                  +{s.transactions.length - 5} more transactions
                </div>
              )}
            </div>
          </div>
        ))}
      </CardContent>
    </Card>
  );
}
