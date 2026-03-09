import { useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";

export default function NotFoundPage() {
  const navigate = useNavigate();

  return (
    <div className="flex h-full items-center justify-center px-4">
      <div className="max-w-md space-y-4 text-center">
        <h1 className="text-4xl font-bold tracking-tight">404</h1>
        <p className="text-sm text-muted-foreground">This page doesn't exist.</p>
        <Button variant="outline" onClick={() => navigate("/")}>
          Go home
        </Button>
      </div>
    </div>
  );
}
