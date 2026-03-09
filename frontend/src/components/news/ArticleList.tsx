import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  Bookmark,
  BookmarkCheck,
  ExternalLink,
  RefreshCw,
  ChevronDown,
  ChevronUp,
} from "lucide-react";
import { formatDistanceToNow } from "date-fns";
import { api } from "@/lib/api";
import type { NewsArticle, PaginatedResponse } from "@/types";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { cn } from "@/lib/utils";

type Filter = "all" | "unread" | "bookmarked";

export function ArticleList() {
  const queryClient = useQueryClient();
  const [filter, setFilter] = useState<Filter>("all");
  const [expandedId, setExpandedId] = useState<number | null>(null);

  const { data, isLoading, isError } = useQuery({
    queryKey: ["articles"],
    queryFn: () => api.get<PaginatedResponse<NewsArticle>>("/news/articles/"),
  });

  const markReadMutation = useMutation({
    mutationFn: ({ id }: { id: number }) =>
      api.patch<NewsArticle>(`/news/articles/${id}/`, { is_read: true }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["articles"] }),
  });

  const toggleBookmarkMutation = useMutation({
    mutationFn: ({ id, current }: { id: number; current: boolean }) =>
      api.patch<NewsArticle>(`/news/articles/${id}/`, { is_bookmarked: !current }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["articles"] }),
  });

  const fetchAllMutation = useMutation({
    mutationFn: () => api.post<{ fetched: number }>("/news/sources/fetch_all/"),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["articles"] }),
  });

  const allArticles = data?.results || [];
  const articles = allArticles.filter((a) => {
    if (filter === "unread") return !a.is_read;
    if (filter === "bookmarked") return a.is_bookmarked;
    return true;
  });

  function handleArticleClick(article: NewsArticle) {
    if (!article.is_read) {
      markReadMutation.mutate({ id: article.id });
    }
    setExpandedId(expandedId === article.id ? null : article.id);
  }

  if (isLoading) {
    return (
      <div className="space-y-3">
        {Array.from({ length: 4 }).map((_, i) => (
          <Skeleton key={i} className="h-24 w-full rounded-lg" />
        ))}
      </div>
    );
  }

  if (isError) {
    return (
      <div className="py-8 text-center text-sm text-muted-foreground">
        Failed to load articles. Try again later.
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div className="flex gap-2">
          {(["all", "unread", "bookmarked"] as Filter[]).map((f) => (
            <Button
              key={f}
              variant={filter === f ? "default" : "outline"}
              size="sm"
              onClick={() => setFilter(f)}
            >
              {f === "all" ? "All" : f === "unread" ? "Unread" : "Bookmarked"}
            </Button>
          ))}
        </div>
        <Button
          variant="outline"
          size="sm"
          disabled={fetchAllMutation.isPending}
          onClick={() => fetchAllMutation.mutate()}
        >
          <RefreshCw className={cn("mr-2 h-4 w-4", fetchAllMutation.isPending && "animate-spin")} />
          {fetchAllMutation.isPending ? "Refreshing..." : "Refresh"}
        </Button>
      </div>

      {articles.length === 0 ? (
        <div className="py-12 text-center text-muted-foreground">
          {filter === "all"
            ? "No articles yet. Add news sources and they'll appear here."
            : `No ${filter} articles.`}
        </div>
      ) : (
        <div className="space-y-3">
          {articles.map((article) => {
            const isExpanded = expandedId === article.id;
            return (
              <Card key={article.id} className="overflow-hidden">
                <CardContent className="p-4">
                  <div className="flex items-start gap-3">
                    <div className="flex-1 min-w-0">
                      <button
                        onClick={() => handleArticleClick(article)}
                        className={cn(
                          "text-left text-sm hover:underline flex items-center gap-1",
                          !article.is_read ? "font-semibold" : "font-normal text-muted-foreground"
                        )}
                      >
                        {article.title}
                        {isExpanded ? (
                          <ChevronUp className="ml-1 inline h-3 w-3 shrink-0" />
                        ) : (
                          <ChevronDown className="ml-1 inline h-3 w-3 shrink-0" />
                        )}
                      </button>
                      <div className="mt-1 flex items-center gap-2 text-xs text-muted-foreground">
                        <span>{article.source_name}</span>
                        <span>
                          {formatDistanceToNow(new Date(article.published_at), { addSuffix: true })}
                        </span>
                      </div>
                      {!isExpanded && article.summary && (
                        <p className="mt-1.5 text-xs text-muted-foreground line-clamp-2">
                          {article.summary}
                        </p>
                      )}
                    </div>
                    <Button
                      variant="ghost"
                      size="icon"
                      className="h-8 w-8 shrink-0"
                      onClick={() =>
                        toggleBookmarkMutation.mutate({
                          id: article.id,
                          current: article.is_bookmarked,
                        })
                      }
                    >
                      {article.is_bookmarked ? (
                        <BookmarkCheck className="h-4 w-4 text-primary" />
                      ) : (
                        <Bookmark className="h-4 w-4" />
                      )}
                    </Button>
                  </div>

                  {isExpanded && (
                    <div className="mt-3 space-y-3">
                      {article.summary && (
                        <p className="text-sm text-muted-foreground leading-relaxed">
                          {article.summary}
                        </p>
                      )}
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => window.open(article.url, "_blank", "noopener,noreferrer")}
                      >
                        <ExternalLink className="mr-2 h-3.5 w-3.5" />
                        Open Article
                      </Button>
                    </div>
                  )}
                </CardContent>
              </Card>
            );
          })}
        </div>
      )}
    </div>
  );
}
