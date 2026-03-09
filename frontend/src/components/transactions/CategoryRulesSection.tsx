import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { Plus, Loader2 } from "lucide-react";
import { api } from "@/lib/api";
import type { CategoryRule, Category, PaginatedResponse } from "@/types";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { RowActions } from "@/components/shared/RowActions";
import { ConfirmDialog } from "@/components/shared/ConfirmDialog";

export function CategoryRulesSection() {
  const queryClient = useQueryClient();
  const [showForm, setShowForm] = useState(false);
  const [pattern, setPattern] = useState("");
  const [categoryId, setCategoryId] = useState("");
  const [deleteRule, setDeleteRule] = useState<CategoryRule | null>(null);
  const [editRule, setEditRule] = useState<CategoryRule | null>(null);

  const { data: rulesData, isLoading } = useQuery({
    queryKey: ["category-rules"],
    queryFn: () => api.get<PaginatedResponse<CategoryRule>>("/transactions/category-rules/"),
  });

  const { data: categoriesData } = useQuery({
    queryKey: ["categories"],
    queryFn: () => api.get<PaginatedResponse<Category>>("/transactions/categories/"),
  });

  const rules = rulesData?.results || [];
  const categories = categoriesData?.results || [];

  const saveMutation = useMutation({
    mutationFn: (data: { pattern: string; category: number }) =>
      editRule
        ? api.put<CategoryRule>(`/transactions/category-rules/${editRule.id}/`, data)
        : api.post<CategoryRule>("/transactions/category-rules/", data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["category-rules"] });
      toast.success(editRule ? "Rule updated" : "Rule created");
      resetForm();
    },
    onError: (err: Error) => toast.error(err.message),
  });

  const deleteMutation = useMutation({
    mutationFn: (id: number) => api.delete(`/transactions/category-rules/${id}/`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["category-rules"] });
      toast.success("Rule deleted");
      setDeleteRule(null);
    },
    onError: (err: Error) => toast.error(err.message),
  });

  function resetForm() {
    setShowForm(false);
    setPattern("");
    setCategoryId("");
    setEditRule(null);
  }

  function handleEdit(rule: CategoryRule) {
    setEditRule(rule);
    setPattern(rule.pattern);
    setCategoryId(String(rule.category));
    setShowForm(true);
  }

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!pattern.trim() || !categoryId) return;
    saveMutation.mutate({ pattern: pattern.trim(), category: Number(categoryId) });
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Category Rules</CardTitle>
        <CardDescription>
          Auto-categorize transactions based on pattern matching. When a transaction description
          matches a pattern, it gets the assigned category.
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        {isLoading ? (
          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            <Loader2 className="h-4 w-4 animate-spin" /> Loading rules...
          </div>
        ) : rules.length > 0 ? (
          <div className="space-y-2">
            {rules.map((rule) => (
              <div
                key={rule.id}
                className="flex items-center justify-between rounded-lg border p-3"
              >
                <div className="flex items-center gap-3">
                  <code className="rounded bg-muted px-2 py-0.5 text-sm">{rule.pattern}</code>
                  <Badge variant="secondary">{rule.category_name}</Badge>
                </div>
                <RowActions onEdit={() => handleEdit(rule)} onDelete={() => setDeleteRule(rule)} />
              </div>
            ))}
          </div>
        ) : (
          <p className="text-sm text-muted-foreground">
            No rules yet. Add one to auto-categorize transactions.
          </p>
        )}

        {showForm ? (
          <form onSubmit={handleSubmit} className="flex items-end gap-3 rounded-lg border p-3">
            <div className="flex-1 space-y-1">
              <label className="text-xs font-medium">Pattern</label>
              <Input
                value={pattern}
                onChange={(e) => setPattern(e.target.value)}
                placeholder="e.g. AMAZON, Starbucks"
                className="h-8 text-sm"
                required
              />
            </div>
            <div className="flex-1 space-y-1">
              <label className="text-xs font-medium">Category</label>
              <Select value={categoryId} onValueChange={setCategoryId}>
                <SelectTrigger className="h-8 text-sm">
                  <SelectValue placeholder="Select..." />
                </SelectTrigger>
                <SelectContent>
                  {categories.map((c) => (
                    <SelectItem key={c.id} value={String(c.id)}>
                      {c.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <Button size="sm" className="h-8" type="submit" disabled={saveMutation.isPending}>
              {saveMutation.isPending ? "Saving..." : editRule ? "Update" : "Save"}
            </Button>
            <Button size="sm" className="h-8" variant="ghost" type="button" onClick={resetForm}>
              Cancel
            </Button>
          </form>
        ) : (
          <Button variant="outline" size="sm" onClick={() => setShowForm(true)}>
            <Plus className="mr-1 h-3 w-3" /> Add Rule
          </Button>
        )}

        <ConfirmDialog
          open={!!deleteRule}
          onOpenChange={(open) => !open && setDeleteRule(null)}
          title="Delete Rule"
          description={`Delete the rule for "${deleteRule?.pattern}"?`}
          onConfirm={() => deleteRule && deleteMutation.mutate(deleteRule.id)}
          destructive
          loading={deleteMutation.isPending}
        />
      </CardContent>
    </Card>
  );
}
