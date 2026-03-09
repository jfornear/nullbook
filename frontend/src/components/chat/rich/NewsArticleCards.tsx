import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ExternalLink } from "lucide-react";
import { formatDistanceToNow } from "date-fns";

interface NewsData {
  articles: {
    id: number;
    title: string;
    source_name: string;
    url: string;
    summary: string;
    published_at: string | null;
  }[];
  total: number;
}

export function NewsArticleCards({ data }: { data: unknown }) {
  const { articles } = data as NewsData;

  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="text-sm">News ({articles.length})</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-3">
          {articles.map((a) => (
            <a
              key={a.id}
              href={a.url}
              target="_blank"
              rel="noopener noreferrer"
              className="block group"
            >
              <div className="text-sm group-hover:underline">
                {a.title}
                <ExternalLink className="ml-1 inline h-3 w-3 text-muted-foreground" />
              </div>
              <div className="flex items-center gap-2 text-xs text-muted-foreground mt-0.5">
                <span>{a.source_name}</span>
                {a.published_at && (
                  <span>
                    {formatDistanceToNow(new Date(a.published_at), {
                      addSuffix: true,
                    })}
                  </span>
                )}
              </div>
              {a.summary && (
                <p className="mt-1 text-xs text-muted-foreground line-clamp-2">{a.summary}</p>
              )}
            </a>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}
