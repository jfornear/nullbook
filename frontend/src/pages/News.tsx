import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { Eye, Plus, ChevronDown, ChevronUp } from "lucide-react";
import { api } from "@/lib/api";
import type { NewsSource, Watchlist, PaginatedResponse } from "@/types";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { CardSkeleton } from "@/components/shared/CardSkeleton";
import { QueryError } from "@/components/shared/QueryError";
import { RowActions } from "@/components/shared/RowActions";
import { ConfirmDialog } from "@/components/shared/ConfirmDialog";
import { ArticleList } from "@/components/news/ArticleList";
import AddNewsSourceDialog from "@/components/news/AddNewsSourceDialog";
import CreateWatchlistDialog from "@/components/news/CreateWatchlistDialog";
import { PresetSourceGrid } from "@/components/news/PresetSourceGrid";
import { PRESET_SOURCES } from "@/components/news/presetSources";

export default function NewsPage() {
  const queryClient = useQueryClient();
  const [sourceDialogOpen, setSourceDialogOpen] = useState(false);
  const [watchlistDialogOpen, setWatchlistDialogOpen] = useState(false);
  const [editSource, setEditSource] = useState<NewsSource | null>(null);
  const [deleteSource, setDeleteSource] = useState<NewsSource | null>(null);
  const [editWatchlist, setEditWatchlist] = useState<Watchlist | null>(null);
  const [deleteWatchlist, setDeleteWatchlist] = useState<Watchlist | null>(null);
  const [showSuggestedSources, setShowSuggestedSources] = useState(false);

  const {
    data: sourcesData,
    isLoading: sourcesLoading,
    isError: sourcesError,
    error: sourcesErrMsg,
    refetch: refetchSources,
  } = useQuery({
    queryKey: ["news-sources"],
    queryFn: () => api.get<PaginatedResponse<NewsSource>>("/news/sources/"),
  });

  const {
    data: watchlistsData,
    isLoading: watchlistsLoading,
    isError: watchlistsError,
    error: watchlistsErrMsg,
    refetch: refetchWatchlists,
  } = useQuery({
    queryKey: ["watchlists"],
    queryFn: () => api.get<PaginatedResponse<Watchlist>>("/news/watchlists/"),
  });

  const deleteSourceMutation = useMutation({
    mutationFn: (id: number) => api.delete(`/news/sources/${id}/`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["news-sources"] });
      toast.success("News source deleted");
      setDeleteSource(null);
    },
    onError: (err: Error) => toast.error(err.message),
  });

  const deleteWatchlistMutation = useMutation({
    mutationFn: (id: number) => api.delete(`/news/watchlists/${id}/`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["watchlists"] });
      toast.success("Watchlist deleted");
      setDeleteWatchlist(null);
    },
    onError: (err: Error) => toast.error(err.message),
  });

  const sources = sourcesData?.results || [];
  const watchlists = watchlistsData?.results || [];
  const hasData = sources.length > 0 || watchlists.length > 0;
  const isLoading = sourcesLoading || watchlistsLoading;
  const isError = sourcesError || watchlistsError;
  const existingUrls = new Set(sources.map((s) => s.url));
  const hasUnadded = PRESET_SOURCES.some((p) => !existingUrls.has(p.url));

  if (isError) {
    return (
      <QueryError
        message={sourcesErrMsg?.message || watchlistsErrMsg?.message}
        onRetry={() => {
          refetchSources();
          refetchWatchlists();
        }}
      />
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <p className="text-muted-foreground">
          {sources.length} source{sources.length !== 1 ? "s" : ""}, {watchlists.length} watchlist
          {watchlists.length !== 1 ? "s" : ""}
        </p>
        <div className="flex gap-2">
          <Button size="sm" onClick={() => setSourceDialogOpen(true)}>
            <Plus className="mr-2 h-4 w-4" />
            Add Source
          </Button>
          <Button size="sm" variant="outline" onClick={() => setWatchlistDialogOpen(true)}>
            <Eye className="mr-2 h-4 w-4" />
            Create Watchlist
          </Button>
        </div>
      </div>

      {isLoading ? (
        <div className="space-y-4">
          {Array.from({ length: 2 }).map((_, i) => (
            <CardSkeleton key={i} />
          ))}
        </div>
      ) : !hasData ? (
        <Card>
          <CardHeader>
            <CardTitle>News and Signals</CardTitle>
            <CardDescription>
              Get started by adding popular sources below, or add a custom RSS feed.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <PresetSourceGrid existingSources={sources} />
            <div className="mt-6 flex gap-3">
              <Button variant="outline" onClick={() => setSourceDialogOpen(true)}>
                <Plus className="mr-2 h-4 w-4" />
                Add custom source
              </Button>
              <Button variant="outline" onClick={() => setWatchlistDialogOpen(true)}>
                <Eye className="mr-2 h-4 w-4" />
                Create watchlist
              </Button>
            </div>
          </CardContent>
        </Card>
      ) : (
        <Tabs defaultValue="articles">
          <TabsList>
            <TabsTrigger value="articles">Articles</TabsTrigger>
            <TabsTrigger value="sources">Sources</TabsTrigger>
            <TabsTrigger value="watchlists">Watchlists</TabsTrigger>
          </TabsList>

          <TabsContent value="articles" className="mt-4">
            <ArticleList />
          </TabsContent>

          <TabsContent value="sources" className="mt-4 space-y-4">
            {sources.length === 0 ? (
              <div className="py-12 text-center text-muted-foreground">No sources yet.</div>
            ) : (
              <div className="space-y-3">
                {sources.map((source) => (
                  <div
                    key={source.id}
                    className="flex items-center justify-between rounded-lg border p-3"
                  >
                    <div>
                      <p className="text-sm font-medium">{source.name}</p>
                      <p className="text-xs text-muted-foreground">{source.feed_url}</p>
                    </div>
                    <div className="flex items-center gap-2">
                      <Badge variant={source.is_active ? "default" : "secondary"}>
                        {source.is_active ? "Active" : "Inactive"}
                      </Badge>
                      <RowActions
                        onEdit={() => setEditSource(source)}
                        onDelete={() => setDeleteSource(source)}
                      />
                    </div>
                  </div>
                ))}
              </div>
            )}
            {hasUnadded && (
              <div>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => setShowSuggestedSources((v) => !v)}
                >
                  {showSuggestedSources ? (
                    <ChevronUp className="mr-1.5 h-4 w-4" />
                  ) : (
                    <ChevronDown className="mr-1.5 h-4 w-4" />
                  )}
                  Browse more sources
                </Button>
                {showSuggestedSources && (
                  <div className="mt-3">
                    <PresetSourceGrid existingSources={sources} />
                  </div>
                )}
              </div>
            )}
          </TabsContent>

          <TabsContent value="watchlists" className="mt-4">
            {watchlists.length === 0 ? (
              <div className="py-12 text-center text-muted-foreground">No watchlists yet.</div>
            ) : (
              <div className="space-y-3">
                {watchlists.map((wl) => (
                  <div
                    key={wl.id}
                    className="flex items-center justify-between rounded-lg border p-3"
                  >
                    <div>
                      <p className="text-sm font-medium">{wl.name}</p>
                      <div className="mt-1 flex flex-wrap gap-1">
                        {wl.keywords
                          .split(",")
                          .map((kw) => kw.trim())
                          .filter(Boolean)
                          .map((kw) => (
                            <Badge key={kw} variant="outline" className="text-xs">
                              {kw}
                            </Badge>
                          ))}
                      </div>
                    </div>
                    <RowActions
                      onEdit={() => setEditWatchlist(wl)}
                      onDelete={() => setDeleteWatchlist(wl)}
                    />
                  </div>
                ))}
              </div>
            )}
          </TabsContent>
        </Tabs>
      )}

      <AddNewsSourceDialog
        open={sourceDialogOpen || !!editSource}
        onOpenChange={(open) => {
          if (!open) {
            setSourceDialogOpen(false);
            setEditSource(null);
          }
        }}
        editSource={editSource}
      />
      <CreateWatchlistDialog
        open={watchlistDialogOpen || !!editWatchlist}
        onOpenChange={(open) => {
          if (!open) {
            setWatchlistDialogOpen(false);
            setEditWatchlist(null);
          }
        }}
        editWatchlist={editWatchlist}
      />

      <ConfirmDialog
        open={!!deleteSource}
        onOpenChange={(open) => !open && setDeleteSource(null)}
        title="Delete News Source"
        description={`Are you sure you want to delete "${deleteSource?.name}"? This action cannot be undone.`}
        onConfirm={() => deleteSource && deleteSourceMutation.mutate(deleteSource.id)}
        destructive
        loading={deleteSourceMutation.isPending}
      />
      <ConfirmDialog
        open={!!deleteWatchlist}
        onOpenChange={(open) => !open && setDeleteWatchlist(null)}
        title="Delete Watchlist"
        description={`Are you sure you want to delete "${deleteWatchlist?.name}"? This action cannot be undone.`}
        onConfirm={() => deleteWatchlist && deleteWatchlistMutation.mutate(deleteWatchlist.id)}
        destructive
        loading={deleteWatchlistMutation.isPending}
      />
    </div>
  );
}
