import { useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { Check, Loader2, Plus } from "lucide-react";
import { api } from "@/lib/api";
import type { NewsSource } from "@/types";
import { Button } from "@/components/ui/button";
import { PRESET_SOURCES } from "./presetSources";

interface Props {
  existingSources: NewsSource[];
}

export function PresetSourceGrid({ existingSources }: Props) {
  const queryClient = useQueryClient();
  const [addingUrl, setAddingUrl] = useState<string | null>(null);

  const addMutation = useMutation({
    mutationFn: (data: { name: string; url: string; feed_url: string }) =>
      api.post<NewsSource>("/news/sources/", data),
    onSuccess: (_data, variables) => {
      queryClient.invalidateQueries({ queryKey: ["news-sources"] });
      queryClient.invalidateQueries({ queryKey: ["articles"] });
      toast.success(`Added ${variables.name}`);
      setAddingUrl(null);
    },
    onError: (err: Error) => {
      toast.error(err.message);
      setAddingUrl(null);
    },
  });

  const existingUrls = new Set(existingSources.map((s) => s.url));

  return (
    <div className="grid gap-3 grid-cols-1 sm:grid-cols-2 lg:grid-cols-3">
      {PRESET_SOURCES.map((preset) => {
        const alreadyAdded = existingUrls.has(preset.url);
        const isAdding = addingUrl === preset.url;

        return (
          <div
            key={preset.url}
            className="flex flex-col justify-between rounded-lg border p-4 hover:bg-accent/50 transition-colors"
          >
            <div>
              <p className="font-medium text-sm">{preset.name}</p>
              <p className="mt-1 text-xs text-muted-foreground">{preset.description}</p>
            </div>
            <div className="mt-3">
              {alreadyAdded ? (
                <Button variant="ghost" size="sm" disabled className="h-8 px-3">
                  <Check className="mr-1.5 h-3.5 w-3.5 text-green-600" />
                  Added
                </Button>
              ) : (
                <Button
                  variant="outline"
                  size="sm"
                  className="h-8 px-3"
                  disabled={isAdding}
                  onClick={() => {
                    setAddingUrl(preset.url);
                    addMutation.mutate({
                      name: preset.name,
                      url: preset.url,
                      feed_url: preset.feed_url,
                    });
                  }}
                >
                  {isAdding ? (
                    <Loader2 className="mr-1.5 h-3.5 w-3.5 animate-spin" />
                  ) : (
                    <Plus className="mr-1.5 h-3.5 w-3.5" />
                  )}
                  {isAdding ? "Adding..." : "Add"}
                </Button>
              )}
            </div>
          </div>
        );
      })}
    </div>
  );
}
