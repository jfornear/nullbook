import { AlertCircle } from "lucide-react";
import { Button } from "@/components/ui/button";

interface QueryErrorProps {
  message?: string;
  onRetry?: () => void;
}

export function QueryError({ message, onRetry }: QueryErrorProps) {
  return (
    <div className="flex flex-col items-center justify-center py-12 text-center">
      <AlertCircle className="mb-3 h-8 w-8 text-muted-foreground" />
      <p className="text-sm font-medium">Failed to load data</p>
      <p className="mt-1 text-xs text-muted-foreground">
        {message || "Something went wrong. Please try again."}
      </p>
      {onRetry && (
        <Button variant="outline" size="sm" onClick={onRetry} className="mt-4">
          Try again
        </Button>
      )}
    </div>
  );
}
