import { useCallback, useEffect, useRef, useState } from "react";
import { useParams, useLocation } from "react-router-dom";
import { useQueryClient } from "@tanstack/react-query";
import { ArrowDown } from "lucide-react";
import { useConversation } from "@/lib/chat";
import { streamChat } from "@/lib/chat-stream";
import { ChatInput } from "./ChatInput";
import { ChatMessage, TypingIndicator } from "./ChatMessage";
import { ChatActionProvider } from "./ChatActionContext";
import { ConversationActions } from "./ConversationActions";
import { Skeleton } from "@/components/ui/skeleton";
import { Button } from "@/components/ui/button";
import type { Message, ToolResult } from "@/types/chat";

function ChatViewInner({ conversationId }: { conversationId: string }) {
  const location = useLocation();
  const { data: conversation, isLoading } = useConversation(conversationId);
  const queryClient = useQueryClient();
  const bottomRef = useRef<HTMLDivElement>(null);
  const scrollContainerRef = useRef<HTMLDivElement>(null);
  const initialMessageSentRef = useRef(false);
  const [showScrollButton, setShowScrollButton] = useState(false);

  // Streaming state
  const [isStreaming, setIsStreaming] = useState(false);
  const [streamingText, setStreamingText] = useState("");
  const [streamingToolResults, setStreamingToolResults] = useState<ToolResult[]>([]);
  const [activeToolName, setActiveToolName] = useState<string | null>(null);
  const [pendingUserMessage, setPendingUserMessage] = useState<string | null>(null);
  const abortControllerRef = useRef<AbortController | null>(null);

  // Cancel any in-progress stream when conversation changes
  useEffect(() => {
    return () => {
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
        abortControllerRef.current = null;
      }
    };
  }, [conversationId]);

  const hasScrolledRef = useRef(false);
  // Reset scroll flag when switching conversations
  useEffect(() => {
    hasScrolledRef.current = false;
  }, [conversationId]);
  useEffect(() => {
    // Only scroll to bottom on initial load, not during streaming
    if (!hasScrolledRef.current && conversation?.messages?.length) {
      bottomRef.current?.scrollIntoView({ behavior: "instant" });
      hasScrolledRef.current = true;
    }
  }, [conversation?.messages]);

  // Show scroll-to-bottom button whenever user can scroll down
  useEffect(() => {
    const el = scrollContainerRef.current;
    if (!el) return;

    const check = () => {
      const distanceFromBottom = el.scrollHeight - el.scrollTop - el.clientHeight;
      setShowScrollButton(distanceFromBottom > 100);
    };

    // Check on scroll
    el.addEventListener("scroll", check, { passive: true });

    // Check when content size changes (streaming, new messages)
    const observer = new ResizeObserver(check);
    observer.observe(el);
    // Also observe the inner content so we catch child growth
    if (el.firstElementChild) observer.observe(el.firstElementChild);

    return () => {
      el.removeEventListener("scroll", check);
      observer.disconnect();
    };
  }, [isLoading]);

  const scrollToBottom = useCallback(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, []);

  const handleSend = useCallback(
    async (content: string, image?: File) => {
      if (!conversationId || isStreaming) return;

      // Abort any existing stream
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }
      const controller = new AbortController();
      abortControllerRef.current = controller;

      setPendingUserMessage(content);
      setIsStreaming(true);
      setStreamingText("");
      setStreamingToolResults([]);
      setActiveToolName(null);

      // Refetch sidebar so the title appears immediately
      queryClient.invalidateQueries({ queryKey: ["conversations"] });

      try {
        await streamChat(
          conversationId,
          content,
          {
            onTextDelta: (text) => {
              setStreamingText((prev) => prev + text);
              setActiveToolName(null);
            },
            onToolStart: (toolName) => {
              setActiveToolName(toolName);
            },
            onToolResult: (_toolUseId, _toolName, result) => {
              setActiveToolName(null);
              const toolResult = result as Record<string, unknown>;
              setStreamingToolResults((prev) => [
                ...prev,
                {
                  tool_use_id: _toolUseId,
                  content: toolResult,
                  component_type: toolResult?.component_type as string | undefined,
                },
              ]);
            },
            onDone: async () => {
              abortControllerRef.current = null;
              setIsStreaming(false);
              setActiveToolName(null);
              // Refetch conversation before clearing streaming content
              // so there's no visual gap where content disappears
              await queryClient.invalidateQueries({
                queryKey: ["conversation", conversationId],
              });
              setPendingUserMessage(null);
              setStreamingText("");
              setStreamingToolResults([]);
              queryClient.invalidateQueries({ queryKey: ["conversations"] });
            },
            onError: (error) => {
              abortControllerRef.current = null;
              setIsStreaming(false);
              setPendingUserMessage(null);
              setActiveToolName(null);
              setStreamingText((prev) => (prev ? `${prev}\n\nError: ${error}` : `Error: ${error}`));
              // Refetch so the saved user message appears in history
              queryClient.invalidateQueries({
                queryKey: ["conversation", conversationId],
              });
              queryClient.invalidateQueries({ queryKey: ["conversations"] });
            },
          },
          image,
          controller.signal
        );
      } catch (err) {
        // Don't update state if aborted (component may be unmounted)
        if (err instanceof DOMException && err.name === "AbortError") return;
        setIsStreaming(false);
        setPendingUserMessage(null);
      }
    },
    [conversationId, isStreaming, queryClient]
  );

  // Auto-send initial message from HomeView navigation
  useEffect(() => {
    const state = location.state as { initialMessage?: string } | null;
    if (state?.initialMessage && conversationId && !initialMessageSentRef.current && !isLoading) {
      initialMessageSentRef.current = true;
      window.history.replaceState({}, "");
      handleSend(state.initialMessage);
    }
  }, [location.state, conversationId, isLoading, handleSend]);

  if (isLoading) {
    return (
      <div className="flex h-full flex-col">
        <div className="flex-1 p-4 md:p-6 space-y-4">
          <Skeleton className="h-12 w-3/4" />
          <Skeleton className="h-12 w-1/2 ml-auto" />
          <Skeleton className="h-12 w-2/3" />
        </div>
      </div>
    );
  }

  const messages = conversation?.messages || [];

  return (
    <ChatActionProvider sendMessage={handleSend}>
      <div className="flex h-full flex-col">
        {/* Header */}
        {conversation && (
          <div className="hidden md:flex h-12 shrink-0 items-center justify-between gap-2 border-b px-4">
            <span className="min-w-0 truncate text-sm font-medium text-muted-foreground">
              {conversation.title || "New conversation"}
            </span>
            <ConversationActions
              id={conversation.id}
              title={conversation.title || "New conversation"}
              isPinned={conversation.is_pinned}
              triggerClassName="h-7 w-7"
            />
          </div>
        )}
        {/* Messages */}
        <div className="relative flex-1 overflow-hidden">
          <div ref={scrollContainerRef} className="h-full overflow-y-auto px-4 md:px-6">
            <div className="mx-auto max-w-3xl">
              {messages.map((msg) => (
                <ChatMessage key={msg.id} message={msg} />
              ))}

              {/* Optimistic user message while streaming */}
              {pendingUserMessage && (
                <ChatMessage
                  message={
                    {
                      id: "pending",
                      role: "user",
                      content: pendingUserMessage,
                      tool_calls: [],
                      tool_results: [],
                      created_at: new Date().toISOString(),
                      conversation: conversationId || "",
                    } satisfies Message
                  }
                />
              )}

              {/* Streaming assistant response (also shown for errors after streaming ends) */}
              {(isStreaming || streamingText) &&
              (streamingText || streamingToolResults.length > 0 || activeToolName) ? (
                <ChatMessage
                  message={
                    {
                      id: "streaming",
                      role: "assistant",
                      content: "",
                      tool_calls: [],
                      tool_results: [],
                      created_at: new Date().toISOString(),
                      conversation: conversationId || "",
                    } satisfies Message
                  }
                  streamContent={streamingText}
                  streamToolResults={streamingToolResults}
                  activeToolName={activeToolName || undefined}
                />
              ) : isStreaming ? (
                <TypingIndicator />
              ) : null}

              <div ref={bottomRef} />
            </div>
          </div>

          {/* Scroll to bottom button */}
          {showScrollButton && (
            <div className="absolute bottom-3 left-0 right-0 flex justify-center pointer-events-none z-10">
              <Button
                variant="outline"
                size="icon"
                className="h-8 w-8 rounded-full shadow-md pointer-events-auto"
                onClick={scrollToBottom}
              >
                <ArrowDown className="h-4 w-4" />
              </Button>
            </div>
          )}
        </div>

        {/* Input */}
        <div className="shrink-0 p-4 pt-2">
          <div className="mx-auto max-w-2xl">
            <ChatInput onSend={handleSend} disabled={isStreaming} autoFocus />
          </div>
        </div>
      </div>
    </ChatActionProvider>
  );
}

export function ChatView() {
  const { conversationId } = useParams<{ conversationId: string }>();
  if (!conversationId) return null;
  return <ChatViewInner key={conversationId} conversationId={conversationId} />;
}
