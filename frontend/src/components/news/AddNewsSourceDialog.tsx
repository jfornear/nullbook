import { useState, useEffect } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { api } from "@/lib/api";
import type { NewsSource } from "@/types";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";

interface Props {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  editSource?: NewsSource | null;
}

export default function AddNewsSourceDialog({ open, onOpenChange, editSource }: Props) {
  const queryClient = useQueryClient();
  const [name, setName] = useState("");
  const [url, setUrl] = useState("");
  const [feedUrl, setFeedUrl] = useState("");
  const [error, setError] = useState("");

  const isEditing = !!editSource;

  useEffect(() => {
    if (editSource) {
      setName(editSource.name);
      setUrl(editSource.url);
      setFeedUrl(editSource.feed_url);
    }
  }, [editSource]);

  const mutation = useMutation({
    mutationFn: (data: Partial<NewsSource>) =>
      isEditing
        ? api.put<NewsSource>(`/news/sources/${editSource!.id}/`, data)
        : api.post<NewsSource>("/news/sources/", data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["news-sources"] });
      queryClient.invalidateQueries({ queryKey: ["articles"] });
      toast.success(isEditing ? "News source updated" : "News source added");
      handleClose();
    },
    onError: (err: Error) => setError(err.message),
  });

  function handleClose() {
    setName("");
    setUrl("");
    setFeedUrl("");
    setError("");
    onOpenChange(false);
  }

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    mutation.mutate({
      name,
      url,
      feed_url: feedUrl,
    });
  }

  return (
    <Dialog open={open} onOpenChange={handleClose}>
      <DialogContent>
        <form onSubmit={handleSubmit}>
          <DialogHeader>
            <DialogTitle>{isEditing ? "Edit News Source" : "Add News Source"}</DialogTitle>
            <DialogDescription>
              {isEditing
                ? "Update news source details."
                : "Subscribe to an RSS or Atom feed to track articles from this source."}
            </DialogDescription>
          </DialogHeader>
          <div className="grid gap-4 py-4">
            <div className="grid gap-2">
              <Label htmlFor="name">Source Name</Label>
              <Input
                id="name"
                placeholder="e.g. Bloomberg Markets"
                value={name}
                onChange={(e) => setName(e.target.value)}
                required
              />
            </div>
            <div className="grid gap-2">
              <Label htmlFor="url">Website URL</Label>
              <Input
                id="url"
                type="url"
                placeholder="https://www.bloomberg.com"
                value={url}
                onChange={(e) => setUrl(e.target.value)}
                required
              />
            </div>
            <div className="grid gap-2">
              <Label htmlFor="feedUrl">Feed URL</Label>
              <Input
                id="feedUrl"
                type="url"
                placeholder="https://www.bloomberg.com/feed/rss"
                value={feedUrl}
                onChange={(e) => setFeedUrl(e.target.value)}
              />
            </div>
            {error && <p className="text-sm text-destructive">{error}</p>}
          </div>
          <DialogFooter>
            <Button type="button" variant="outline" onClick={handleClose}>
              Cancel
            </Button>
            <Button type="submit" disabled={mutation.isPending}>
              {mutation.isPending
                ? isEditing
                  ? "Saving..."
                  : "Adding..."
                : isEditing
                  ? "Save Changes"
                  : "Add Source"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
