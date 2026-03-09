import { useEffect, useRef, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { Pin } from "lucide-react";
import { useConversations } from "@/lib/chat";
import { cn } from "@/lib/utils";
import { Skeleton } from "@/components/ui/skeleton";
import { ConversationActions } from "./ConversationActions";
import type { Conversation } from "@/types/chat";

// Set of conversation IDs that have already had their title animated (persists across re-renders)
const animatedTitles = new Set<string>();

function ConversationTitle({ id, title }: { id: string; title: string }) {
  const [displayTitle, setDisplayTitle] = useState(() => {
    // If already animated or had a title on first render, show immediately
    if (animatedTitles.has(id) || title) {
      animatedTitles.add(id);
      return title;
    }
    return "";
  });
  const prevTitleRef = useRef(title);

  useEffect(() => {
    // Animate only when title transitions from empty to non-empty for the first time
    if (title && !prevTitleRef.current && !animatedTitles.has(id)) {
      animatedTitles.add(id);
      let i = 0;
      setDisplayTitle("");
      const interval = setInterval(() => {
        i++;
        setDisplayTitle(title.slice(0, i));
        if (i >= title.length) clearInterval(interval);
      }, 30);
      prevTitleRef.current = title;
      return () => clearInterval(interval);
    }
    setDisplayTitle(title);
    prevTitleRef.current = title;
  }, [id, title]);

  return <>{displayTitle || "New conversation"}</>;
}

interface ConversationListProps {
  collapsed?: boolean;
}

export function ConversationList({ collapsed }: ConversationListProps) {
  const navigate = useNavigate();
  const { conversationId } = useParams();
  const { data: conversations, isLoading } = useConversations();

  if (collapsed) return null;

  if (isLoading) {
    return (
      <div className="space-y-2 px-2">
        {Array.from({ length: 3 }).map((_, i) => (
          <Skeleton key={i} className="h-10 w-full rounded-md" />
        ))}
      </div>
    );
  }

  if (!conversations?.length) {
    return (
      <div className="px-4 py-6 text-center text-xs text-muted-foreground">
        No conversations yet
      </div>
    );
  }

  // Group conversations: Pinned, Today, Previous
  const today = new Date();
  const pinned = conversations.filter((c) => c.is_pinned);
  const unpinned = conversations.filter((c) => !c.is_pinned);
  const todayItems = unpinned.filter(
    (c) => new Date(c.updated_at).toDateString() === today.toDateString()
  );
  const olderItems = unpinned.filter(
    (c) => new Date(c.updated_at).toDateString() !== today.toDateString()
  );

  const groups: { label: string; items: Conversation[] }[] = [];
  if (pinned.length) groups.push({ label: "Pinned", items: pinned });
  if (todayItems.length) groups.push({ label: "Today", items: todayItems });
  if (olderItems.length) groups.push({ label: "Previous", items: olderItems });

  return (
    <div className="h-full overflow-y-auto">
      <div className="space-y-4 px-2 py-2">
        {groups.map((group) => (
          <div key={group.label}>
            <div className="mb-1 px-2 text-[11px] font-medium uppercase tracking-wider text-muted-foreground">
              {group.label}
            </div>
            <div className="space-y-0.5">
              {group.items.map((convo) => (
                <div
                  role="button"
                  tabIndex={0}
                  key={convo.id}
                  className={cn(
                    "group flex w-full items-center gap-2 rounded-md px-2 py-1.5 text-sm text-left cursor-pointer hover:bg-accent overflow-hidden",
                    conversationId === convo.id && "bg-accent"
                  )}
                  onClick={() => navigate(`/c/${convo.id}`)}
                  onKeyDown={(e) => {
                    if (e.key === "Enter" || e.key === " ") {
                      e.preventDefault();
                      navigate(`/c/${convo.id}`);
                    }
                  }}
                >
                  {convo.is_pinned && <Pin className="h-3 w-3 shrink-0 text-muted-foreground" />}
                  <span className="min-w-0 flex-1 truncate">
                    <ConversationTitle id={convo.id} title={convo.title} />
                  </span>
                  <div className="shrink-0 opacity-0 group-hover:opacity-100 focus-within:opacity-100">
                    <ConversationActions
                      id={convo.id}
                      title={convo.title || "New conversation"}
                      isPinned={convo.is_pinned}
                    />
                  </div>
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
