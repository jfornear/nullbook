import { useQuery } from "@tanstack/react-query";
import { X } from "lucide-react";
import { api } from "@/lib/api";
import type { Account, Category, PaginatedResponse } from "@/types";
import { Button } from "@/components/ui/button";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { DateRangePicker } from "@/components/shared/DateRangePicker";

interface Filters {
  dateFrom?: string;
  dateTo?: string;
  account?: string;
  category?: string;
  type?: string;
}

interface Props {
  filters: Filters;
  onChange: (filters: Filters) => void;
}

export function TransactionFilters({ filters, onChange }: Props) {
  const { data: accountsData } = useQuery({
    queryKey: ["accounts"],
    queryFn: () => api.get<PaginatedResponse<Account>>("/accounts/accounts/"),
  });

  const { data: categoriesData } = useQuery({
    queryKey: ["categories"],
    queryFn: () => api.get<PaginatedResponse<Category>>("/transactions/categories/"),
  });

  const accounts = accountsData?.results || [];
  const categories = categoriesData?.results || [];

  const hasFilters =
    filters.dateFrom || filters.dateTo || filters.account || filters.category || filters.type;

  return (
    <div className="flex flex-wrap items-center gap-2">
      <DateRangePicker
        from={filters.dateFrom}
        to={filters.dateTo}
        onChange={({ from, to }) => onChange({ ...filters, dateFrom: from, dateTo: to })}
      />

      <Select
        value={filters.account || "all"}
        onValueChange={(v) => onChange({ ...filters, account: v === "all" ? undefined : v })}
      >
        <SelectTrigger className="h-9 w-auto min-w-[140px] text-xs">
          <SelectValue placeholder="All accounts" />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="all">All accounts</SelectItem>
          {accounts.map((a) => (
            <SelectItem key={a.id} value={String(a.id)}>
              {a.name}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>

      <Select
        value={filters.category || "all"}
        onValueChange={(v) => onChange({ ...filters, category: v === "all" ? undefined : v })}
      >
        <SelectTrigger className="h-9 w-auto min-w-[140px] text-xs">
          <SelectValue placeholder="All categories" />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="all">All categories</SelectItem>
          {categories.map((c) => (
            <SelectItem key={c.id} value={String(c.id)}>
              {c.name}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>

      <Select
        value={filters.type || "all"}
        onValueChange={(v) => onChange({ ...filters, type: v === "all" ? undefined : v })}
      >
        <SelectTrigger className="h-9 w-auto min-w-[100px] text-xs">
          <SelectValue placeholder="All types" />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="all">All types</SelectItem>
          <SelectItem value="income">Income</SelectItem>
          <SelectItem value="expense">Expense</SelectItem>
          <SelectItem value="transfer">Transfer</SelectItem>
        </SelectContent>
      </Select>

      {hasFilters && (
        <Button
          variant="ghost"
          size="sm"
          className="h-9 text-xs"
          onClick={() =>
            onChange({
              dateFrom: undefined,
              dateTo: undefined,
              account: undefined,
              category: undefined,
              type: undefined,
            })
          }
        >
          <X className="mr-1 h-3 w-3" />
          Clear
        </Button>
      )}
    </div>
  );
}
