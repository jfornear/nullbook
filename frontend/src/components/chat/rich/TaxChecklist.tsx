import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ClipboardCheck, CheckCircle2, Circle, AlertCircle } from "lucide-react";

interface ChecklistItem {
  label: string;
  status: "complete" | "incomplete" | "review";
  detail: string;
}

interface ChecklistSection {
  section: string;
  items: ChecklistItem[];
}

interface TaxChecklistData {
  tax_year: number;
  sections: ChecklistSection[];
  progress: {
    complete: number;
    total: number;
    percentage: number;
  };
}

const statusIcons: Record<string, typeof CheckCircle2> = {
  complete: CheckCircle2,
  incomplete: Circle,
  review: AlertCircle,
};

const statusColors: Record<string, string> = {
  complete: "text-green-600",
  incomplete: "text-muted-foreground",
  review: "text-amber-500",
};

export function TaxChecklist({ data }: { data: unknown }) {
  const d = data as TaxChecklistData;

  return (
    <Card>
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between">
          <CardTitle className="flex items-center gap-2 text-sm">
            <ClipboardCheck className="h-4 w-4" />
            {d.tax_year} Tax Prep Checklist
          </CardTitle>
          <span className="text-xs font-medium">
            {d.progress.complete}/{d.progress.total} ({d.progress.percentage}%)
          </span>
        </div>
        {/* Progress bar */}
        <div className="h-2 w-full rounded-full bg-muted mt-1">
          <div
            className="h-2 rounded-full bg-green-600 transition-all"
            style={{ width: `${d.progress.percentage}%` }}
          />
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        {d.sections.map((section) => (
          <div key={section.section}>
            <div className="text-xs font-medium text-muted-foreground uppercase tracking-wide mb-1.5">
              {section.section}
            </div>
            <div className="space-y-1">
              {section.items.map((item, i) => {
                const Icon = statusIcons[item.status] || Circle;
                return (
                  <div key={i} className="flex items-start gap-2 rounded-md px-2 py-1.5 text-sm">
                    <Icon className={`h-4 w-4 mt-0.5 shrink-0 ${statusColors[item.status]}`} />
                    <div className="flex-1 min-w-0">
                      <div className="font-medium">{item.label}</div>
                      <div className="text-xs text-muted-foreground">{item.detail}</div>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        ))}
      </CardContent>
    </Card>
  );
}
