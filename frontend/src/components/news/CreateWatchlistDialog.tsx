import { useState, useEffect } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { api } from "@/lib/api";
import type { Watchlist } from "@/types";
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
  editWatchlist?: Watchlist | null;
}

export default function CreateWatchlistDialog({ open, onOpenChange, editWatchlist }: Props) {
  const queryClient = useQueryClient();
  const [name, setName] = useState("");
  const [keywordsInput, setKeywordsInput] = useState("");
  const [error, setError] = useState("");

  const isEditing = !!editWatchlist;

  useEffect(() => {
    if (editWatchlist) {
      setName(editWatchlist.name);
      setKeywordsInput(editWatchlist.keywords);
    }
  }, [editWatchlist]);

  const mutation = useMutation({
    mutationFn: (data: { name: string; keywords: string }) =>
      isEditing
        ? api.put<Watchlist>(`/news/watchlists/${editWatchlist!.id}/`, data)
        : api.post<Watchlist>("/news/watchlists/", data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["watchlists"] });
      toast.success(isEditing ? "Watchlist updated" : "Watchlist created");
      handleClose();
    },
    onError: (err: Error) => setError(err.message),
  });

  function handleClose() {
    setName("");
    setKeywordsInput("");
    setError("");
    onOpenChange(false);
  }

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    mutation.mutate({ name, keywords: keywordsInput });
  }

  return (
    <Dialog open={open} onOpenChange={handleClose}>
      <DialogContent>
        <form onSubmit={handleSubmit}>
          <DialogHeader>
            <DialogTitle>{isEditing ? "Edit Watchlist" : "Create Watchlist"}</DialogTitle>
            <DialogDescription>
              {isEditing
                ? "Update watchlist details."
                : "Monitor articles matching specific keywords across all your news sources."}
            </DialogDescription>
          </DialogHeader>
          <div className="grid gap-4 py-4">
            <div className="grid gap-2">
              <Label htmlFor="name">Watchlist Name</Label>
              <Input
                id="name"
                placeholder="e.g. Tech Earnings"
                value={name}
                onChange={(e) => setName(e.target.value)}
                required
              />
            </div>
            <div className="grid gap-2">
              <Label htmlFor="keywords">Keywords</Label>
              <Input
                id="keywords"
                placeholder="e.g. AAPL, Apple, iPhone"
                value={keywordsInput}
                onChange={(e) => setKeywordsInput(e.target.value)}
                required
              />
              <p className="text-xs text-muted-foreground">Separate keywords with commas</p>
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
                  : "Creating..."
                : isEditing
                  ? "Save Changes"
                  : "Create Watchlist"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
