import { useState, useEffect } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { Loader2 } from "lucide-react";
import { api } from "@/lib/api";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Switch } from "@/components/ui/switch";

interface EmailRule {
  id: number;
  name: string;
  from_pattern: string;
  subject_pattern: string;
  has_attachment?: boolean;
  action: string;
  is_active: boolean;
}

interface Props {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  editRule?: EmailRule | null;
}

const ACTIONS = [
  { value: "process_receipt", label: "Process as Receipt" },
  { value: "ignore", label: "Ignore" },
  { value: "archive", label: "Archive" },
];

export function CreateEmailRuleDialog({ open, onOpenChange, editRule }: Props) {
  const queryClient = useQueryClient();
  const isEdit = !!editRule;

  const [form, setForm] = useState({
    name: "",
    from_pattern: "",
    subject_pattern: "",
    has_attachment: false,
    action: "process_receipt",
    is_active: true,
  });

  useEffect(() => {
    if (editRule) {
      setForm({
        name: editRule.name,
        from_pattern: editRule.from_pattern || "",
        subject_pattern: editRule.subject_pattern || "",
        has_attachment: editRule.has_attachment || false,
        action: editRule.action,
        is_active: editRule.is_active,
      });
    } else {
      setForm({
        name: "",
        from_pattern: "",
        subject_pattern: "",
        has_attachment: false,
        action: "process_receipt",
        is_active: true,
      });
    }
  }, [editRule, open]);

  const mutation = useMutation({
    mutationFn: (data: typeof form) =>
      isEdit
        ? api.patch(`/email-sync/rules/${editRule!.id}/`, data)
        : api.post("/email-sync/rules/", data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["email-rules"] });
      toast.success(isEdit ? "Rule updated" : "Rule created");
      onOpenChange(false);
    },
    onError: (err: Error) => toast.error(err.message),
  });

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>{isEdit ? "Edit Email Rule" : "Add Email Rule"}</DialogTitle>
          <DialogDescription>
            Define patterns to automatically process receipt emails.
          </DialogDescription>
        </DialogHeader>
        <form
          onSubmit={(e) => {
            e.preventDefault();
            mutation.mutate(form);
          }}
          className="space-y-3 pt-2"
        >
          <div className="space-y-2">
            <Label htmlFor="name">Rule Name</Label>
            <Input
              id="name"
              placeholder="e.g. Amazon receipts"
              value={form.name}
              onChange={(e) => setForm((f) => ({ ...f, name: e.target.value }))}
              required
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="from_pattern">From Pattern</Label>
            <Input
              id="from_pattern"
              placeholder="e.g. receipts@amazon.com"
              value={form.from_pattern}
              onChange={(e) => setForm((f) => ({ ...f, from_pattern: e.target.value }))}
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="subject_pattern">Subject Pattern</Label>
            <Input
              id="subject_pattern"
              placeholder="e.g. Your order"
              value={form.subject_pattern}
              onChange={(e) => setForm((f) => ({ ...f, subject_pattern: e.target.value }))}
            />
          </div>
          <div className="flex items-center justify-between">
            <Label htmlFor="has_attachment">Must have attachment</Label>
            <Switch
              id="has_attachment"
              checked={form.has_attachment}
              onCheckedChange={(v) => setForm((f) => ({ ...f, has_attachment: v }))}
            />
          </div>
          <div className="space-y-2">
            <Label>Action</Label>
            <Select
              value={form.action}
              onValueChange={(v) => setForm((f) => ({ ...f, action: v }))}
            >
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {ACTIONS.map((a) => (
                  <SelectItem key={a.value} value={a.value}>
                    {a.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <div className="flex items-center justify-between">
            <Label htmlFor="is_active">Active</Label>
            <Switch
              id="is_active"
              checked={form.is_active}
              onCheckedChange={(v) => setForm((f) => ({ ...f, is_active: v }))}
            />
          </div>
          <div className="flex justify-end gap-2 pt-2">
            <Button type="button" variant="outline" onClick={() => onOpenChange(false)}>
              Cancel
            </Button>
            <Button type="submit" disabled={mutation.isPending}>
              {mutation.isPending && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
              {isEdit ? "Save" : "Add"}
            </Button>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  );
}
