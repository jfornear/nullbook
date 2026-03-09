import { useState } from "react";
import { format } from "date-fns";
import { CalendarDays } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import { Input } from "@/components/ui/input";
import { cn } from "@/lib/utils";

interface Props {
  from?: string;
  to?: string;
  onChange: (range: { from?: string; to?: string }) => void;
}

export function DateRangePicker({ from, to, onChange }: Props) {
  const [open, setOpen] = useState(false);
  const [localFrom, setLocalFrom] = useState(from || "");
  const [localTo, setLocalTo] = useState(to || "");

  function handleApply() {
    onChange({ from: localFrom || undefined, to: localTo || undefined });
    setOpen(false);
  }

  function handleClear() {
    setLocalFrom("");
    setLocalTo("");
    onChange({ from: undefined, to: undefined });
    setOpen(false);
  }

  const label =
    from && to
      ? `${format(new Date(from), "MMM d")} - ${format(new Date(to), "MMM d")}`
      : from
        ? `From ${format(new Date(from), "MMM d")}`
        : to
          ? `Until ${format(new Date(to), "MMM d")}`
          : "Date range";

  return (
    <Popover open={open} onOpenChange={setOpen}>
      <PopoverTrigger asChild>
        <Button
          variant="outline"
          size="sm"
          className={cn("h-9 gap-2 text-xs", (from || to) && "text-foreground")}
        >
          <CalendarDays className="h-3.5 w-3.5" />
          {label}
        </Button>
      </PopoverTrigger>
      <PopoverContent className="w-auto p-4" align="start">
        <div className="grid gap-3">
          <div className="grid gap-1.5">
            <label className="text-xs font-medium">From</label>
            <Input
              type="date"
              value={localFrom}
              onChange={(e) => setLocalFrom(e.target.value)}
              className="h-8 text-xs"
            />
          </div>
          <div className="grid gap-1.5">
            <label className="text-xs font-medium">To</label>
            <Input
              type="date"
              value={localTo}
              onChange={(e) => setLocalTo(e.target.value)}
              className="h-8 text-xs"
            />
          </div>
          <div className="flex gap-2">
            <Button
              size="sm"
              variant="outline"
              className="flex-1 h-8 text-xs"
              onClick={handleClear}
            >
              Clear
            </Button>
            <Button size="sm" className="flex-1 h-8 text-xs" onClick={handleApply}>
              Apply
            </Button>
          </div>
        </div>
      </PopoverContent>
    </Popover>
  );
}
