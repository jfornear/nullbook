import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { TrendingUp, BarChart3, PieChart, Plus } from "lucide-react";
import { api } from "@/lib/api";
import type { Holding, PaginatedResponse } from "@/types";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { formatCurrency } from "@/lib/utils";
import { TableSkeleton } from "@/components/shared/TableSkeleton";
import { QueryError } from "@/components/shared/QueryError";
import { RowActions } from "@/components/shared/RowActions";
import { ConfirmDialog } from "@/components/shared/ConfirmDialog";
import { PortfolioSummaryRow } from "@/components/portfolio/PortfolioSummaryRow";
import { AllocationChart } from "@/components/portfolio/AllocationChart";
import { PerformanceTab } from "@/components/portfolio/PerformanceTab";
import AddHoldingDialog from "@/components/portfolio/AddHoldingDialog";

const features = [
  {
    icon: TrendingUp,
    title: "Track holdings",
    description:
      "Add any security and track shares and cost basis across stocks, ETFs, mutual funds, bonds, and crypto.",
  },
  {
    icon: PieChart,
    title: "See allocation",
    description:
      "Visualize how your portfolio is distributed across asset types, sectors, and accounts.",
  },
  {
    icon: BarChart3,
    title: "Monitor performance",
    description: "Track gains and losses over time with price history and trade records.",
  },
];

export default function PortfolioPage() {
  const queryClient = useQueryClient();
  const [dialogOpen, setDialogOpen] = useState(false);
  const [editHolding, setEditHolding] = useState<Holding | null>(null);
  const [deleteHolding, setDeleteHolding] = useState<Holding | null>(null);

  const { data, isLoading, isError, error, refetch } = useQuery({
    queryKey: ["holdings"],
    queryFn: () => api.get<PaginatedResponse<Holding>>("/portfolio/holdings/"),
  });

  const deleteMutation = useMutation({
    mutationFn: (id: number) => api.delete(`/portfolio/holdings/${id}/`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["holdings"] });
      queryClient.invalidateQueries({ queryKey: ["dashboard"] });
      queryClient.invalidateQueries({ queryKey: ["allocation"] });
      toast.success("Holding deleted");
      setDeleteHolding(null);
    },
    onError: (err: Error) => toast.error(err.message),
  });

  const holdings = data?.results || [];

  if (isError) {
    return <QueryError message={error?.message} onRetry={refetch} />;
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <p className="text-muted-foreground">
          {holdings.length} holding{holdings.length !== 1 ? "s" : ""}
        </p>
        <Button size="sm" onClick={() => setDialogOpen(true)}>
          <Plus className="mr-2 h-4 w-4" />
          Add Holding
        </Button>
      </div>

      {isLoading ? (
        <TableSkeleton rows={6} cols={4} />
      ) : holdings.length === 0 ? (
        <Card>
          <CardHeader>
            <CardTitle>Your complete investment picture</CardTitle>
            <CardDescription>
              Add holdings from brokerage accounts, retirement funds, and crypto wallets to track
              performance and allocation in one place.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid gap-3 sm:grid-cols-3">
              {features.map((feature) => (
                <div
                  key={feature.title}
                  className="flex flex-col items-start rounded-lg border p-4"
                >
                  <div className="mb-3 flex h-9 w-9 items-center justify-center rounded-lg bg-secondary">
                    <feature.icon className="h-4 w-4" />
                  </div>
                  <p className="font-medium">{feature.title}</p>
                  <p className="mt-1 text-sm text-muted-foreground">{feature.description}</p>
                </div>
              ))}
            </div>
            <div className="mt-6">
              <Button onClick={() => setDialogOpen(true)}>
                <Plus className="mr-2 h-4 w-4" />
                Add your first holding
              </Button>
            </div>
          </CardContent>
        </Card>
      ) : (
        <>
          <PortfolioSummaryRow holdings={holdings} />

          <Tabs defaultValue="holdings">
            <TabsList>
              <TabsTrigger value="holdings">Holdings</TabsTrigger>
              <TabsTrigger value="performance">Performance</TabsTrigger>
              <TabsTrigger value="allocation">Allocation</TabsTrigger>
            </TabsList>

            <TabsContent value="holdings" className="mt-4">
              <div className="overflow-x-auto">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Symbol</TableHead>
                      <TableHead>Name</TableHead>
                      <TableHead className="hidden md:table-cell">Account</TableHead>
                      <TableHead className="text-right">Shares</TableHead>
                      <TableHead className="text-right">Cost Basis</TableHead>
                      <TableHead className="w-10" />
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {holdings.map((holding) => (
                      <TableRow
                        key={holding.id}
                        className="cursor-pointer"
                        onClick={() => setEditHolding(holding)}
                      >
                        <TableCell className="font-medium">{holding.security_symbol}</TableCell>
                        <TableCell>{holding.security_name}</TableCell>
                        <TableCell className="hidden md:table-cell text-muted-foreground">
                          {holding.account_name || "-"}
                        </TableCell>
                        <TableCell className="text-right">
                          {parseFloat(holding.shares).toLocaleString()}
                        </TableCell>
                        <TableCell className="text-right">
                          {formatCurrency(holding.cost_basis)}
                        </TableCell>
                        <TableCell onClick={(e) => e.stopPropagation()}>
                          <RowActions
                            onEdit={() => setEditHolding(holding)}
                            onDelete={() => setDeleteHolding(holding)}
                          />
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </div>
            </TabsContent>

            <TabsContent value="performance" className="mt-4">
              <PerformanceTab />
            </TabsContent>

            <TabsContent value="allocation" className="mt-4">
              <AllocationChart />
            </TabsContent>
          </Tabs>
        </>
      )}

      <AddHoldingDialog
        open={dialogOpen || !!editHolding}
        onOpenChange={(open) => {
          if (!open) {
            setDialogOpen(false);
            setEditHolding(null);
          }
        }}
        editHolding={editHolding}
      />

      <ConfirmDialog
        open={!!deleteHolding}
        onOpenChange={(open) => !open && setDeleteHolding(null)}
        title="Delete Holding"
        description={`Are you sure you want to delete ${deleteHolding?.security_symbol}? This action cannot be undone.`}
        onConfirm={() => deleteHolding && deleteMutation.mutate(deleteHolding.id)}
        destructive
        loading={deleteMutation.isPending}
      />
    </div>
  );
}
