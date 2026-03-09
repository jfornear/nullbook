import { useEffect } from "react";
import { Routes, Route } from "react-router-dom";
import { ChatLayout } from "./components/layout/ChatLayout";
import { ErrorBoundary } from "./components/ErrorBoundary";
import { useSession, initCsrf } from "./lib/auth";
import LoginPage from "./pages/Login";
import NotFoundPage from "./pages/NotFound";
import { HomeView } from "./components/chat/HomeView";
import { ChatView } from "./components/chat/ChatView";

export default function App() {
  useEffect(() => {
    initCsrf();
  }, []);

  const { data: user, isLoading, isError } = useSession();

  // Show login only when session check has completed and failed.
  // While loading, render the app optimistically (local-first, usually logged in).
  if (!isLoading && (isError || !user)) {
    return <LoginPage />;
  }

  return (
    <ErrorBoundary>
      <Routes>
        <Route element={<ChatLayout />}>
          <Route path="/" element={<HomeView />} />
          <Route path="/c/:conversationId" element={<ChatView />} />
          <Route path="*" element={<NotFoundPage />} />
        </Route>
      </Routes>
    </ErrorBoundary>
  );
}
