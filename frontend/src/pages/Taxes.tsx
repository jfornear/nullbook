import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { FileText, Receipt, Calculator, Plus } from "lucide-react";
import { api } from "@/lib/api";
import type { TaxYear, PaginatedResponse } from "@/types";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { CardSkeleton } from "@/components/shared/CardSkeleton";
import { QueryError } from "@/components/shared/QueryError";
import { RowActions } from "@/components/shared/RowActions";
import { ConfirmDialog } from "@/components/shared/ConfirmDialog";
import { TaxYearDetailSheet } from "@/components/taxes/TaxYearDetailSheet";
import CreateTaxYearDialog from "@/components/taxes/CreateTaxYearDialog";

const steps = [
  {
    icon: FileText,
    title: "Collect tax documents",
    description:
      "Add your W-2s, 1099s (INT, DIV, B, NEC), 1098s, and K-1s as you receive them. Track which documents you're still waiting for.",
  },
  {
    icon: Receipt,
    title: "Track deductible expenses",
    description:
      "Log mortgage interest, charitable donations, medical costs, business expenses, and other deductibles throughout the year.",
  },
  {
    icon: Calculator,
    title: "Estimate your taxes",
    description:
      "See your total income, deductions, and estimated tax obligation by year. Compare filing statuses to optimize your return.",
  },
];

export default function TaxesPage() {
  const queryClient = useQueryClient();
  const [dialogOpen, setDialogOpen] = useState(false);
  const [editTaxYear, setEditTaxYear] = useState<TaxYear | null>(null);
  const [deleteTaxYear, setDeleteTaxYear] = useState<TaxYear | null>(null);
  const [selectedTaxYear, setSelectedTaxYear] = useState<TaxYear | null>(null);

  const { data, isLoading, isError, error, refetch } = useQuery({
    queryKey: ["tax-years"],
    queryFn: () => api.get<PaginatedResponse<TaxYear>>("/taxes/tax-years/"),
  });

  const deleteMutation = useMutation({
    mutationFn: (id: number) => api.delete(`/taxes/tax-years/${id}/`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["tax-years"] });
      toast.success("Tax year deleted");
      setDeleteTaxYear(null);
      setSelectedTaxYear(null);
    },
    onError: (err: Error) => toast.error(err.message),
  });

  const taxYears = data?.results || [];

  if (isError) {
    return <QueryError message={error?.message} onRetry={refetch} />;
  }

  function handleEditFromSheet(ty: TaxYear) {
    setSelectedTaxYear(null);
    setEditTaxYear(ty);
  }

  function handleDeleteFromSheet(ty: TaxYear) {
    setSelectedTaxYear(null);
    setDeleteTaxYear(ty);
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <p className="text-muted-foreground">
          {taxYears.length} tax year{taxYears.length !== 1 ? "s" : ""}
        </p>
        <Button size="sm" onClick={() => setDialogOpen(true)}>
          <Plus className="mr-2 h-4 w-4" />
          Create Tax Year
        </Button>
      </div>

      {isLoading ? (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {Array.from({ length: 3 }).map((_, i) => (
            <CardSkeleton key={i} />
          ))}
        </div>
      ) : taxYears.length === 0 ? (
        <Card>
          <CardHeader>
            <CardTitle>Stay on top of tax season</CardTitle>
            <CardDescription>
              Track documents, deductions, and estimated obligations all year round so nothing slips
              through the cracks.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid gap-3 sm:grid-cols-3">
              {steps.map((step) => (
                <div key={step.title} className="flex flex-col items-start rounded-lg border p-4">
                  <div className="mb-3 flex h-9 w-9 items-center justify-center rounded-lg bg-secondary">
                    <step.icon className="h-4 w-4" />
                  </div>
                  <p className="font-medium">{step.title}</p>
                  <p className="mt-1 text-sm text-muted-foreground">{step.description}</p>
                </div>
              ))}
            </div>
            <div className="mt-6">
              <Button onClick={() => setDialogOpen(true)}>
                <Plus className="mr-2 h-4 w-4" />
                Create tax year
              </Button>
            </div>
          </CardContent>
        </Card>
      ) : (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {taxYears.map((ty) => (
            <Card
              key={ty.id}
              className="cursor-pointer transition-colors hover:bg-accent/50"
              onClick={() => setSelectedTaxYear(ty)}
            >
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-base font-medium">{ty.year}</CardTitle>
                <div className="flex items-center gap-1" onClick={(e) => e.stopPropagation()}>
                  <Badge variant="secondary">{ty.filing_status.replace(/_/g, " ")}</Badge>
                  <RowActions
                    onEdit={() => setEditTaxYear(ty)}
                    onDelete={() => setDeleteTaxYear(ty)}
                  />
                </div>
              </CardHeader>
              <CardContent>
                <p className="text-xs text-muted-foreground">
                  Created {new Date(ty.created_at).toLocaleDateString()}
                </p>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      <CreateTaxYearDialog
        open={dialogOpen || !!editTaxYear}
        onOpenChange={(open) => {
          if (!open) {
            setDialogOpen(false);
            setEditTaxYear(null);
          }
        }}
        editTaxYear={editTaxYear}
      />

      <TaxYearDetailSheet
        taxYear={selectedTaxYear}
        open={!!selectedTaxYear}
        onOpenChange={(open) => !open && setSelectedTaxYear(null)}
        onEdit={handleEditFromSheet}
        onDelete={handleDeleteFromSheet}
      />

      <ConfirmDialog
        open={!!deleteTaxYear}
        onOpenChange={(open) => !open && setDeleteTaxYear(null)}
        title="Delete Tax Year"
        description={`Are you sure you want to delete tax year ${deleteTaxYear?.year}? All associated documents and deductions will be lost.`}
        onConfirm={() => deleteTaxYear && deleteMutation.mutate(deleteTaxYear.id)}
        destructive
        loading={deleteMutation.isPending}
      />
    </div>
  );
}
