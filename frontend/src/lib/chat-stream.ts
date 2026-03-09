import { getCsrfToken } from "./api";
import type { StreamEvent } from "@/types/chat";

const API_BASE = import.meta.env.VITE_API_URL || "";

interface StreamCallbacks {
  onTextDelta: (text: string) => void;
  onToolStart: (toolName: string, toolUseId: string) => void;
  onToolResult: (toolUseId: string, toolName: string, result: unknown) => void;
  onDone: () => void;
  onError: (error: string) => void;
}

export async function streamChat(
  conversationId: string,
  content: string,
  callbacks: StreamCallbacks,
  image?: File,
  signal?: AbortSignal
): Promise<void> {
  const csrfToken = getCsrfToken();

  const headers: Record<string, string> = {};
  let body: BodyInit;

  if (image) {
    // Use FormData for multipart upload — let browser set Content-Type with boundary
    const formData = new FormData();
    formData.append("content", content);
    formData.append("image", image);
    body = formData;
  } else {
    headers["Content-Type"] = "application/json";
    body = JSON.stringify({ content });
  }

  if (csrfToken) {
    headers["X-CSRFToken"] = csrfToken;
  }

  const response = await fetch(`${API_BASE}/api/chat/conversations/${conversationId}/stream/`, {
    method: "POST",
    credentials: "include",
    headers,
    body,
    signal,
  });

  if (!response.ok) {
    const err = await response.json().catch(() => ({ detail: response.statusText }));
    callbacks.onError(err.detail || `API error: ${response.status}`);
    callbacks.onDone();
    return;
  }

  const reader = response.body?.getReader();
  if (!reader) {
    callbacks.onError("No response body");
    callbacks.onDone();
    return;
  }

  const decoder = new TextDecoder();
  let buffer = "";

  try {
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });

      // Process complete SSE lines
      const lines = buffer.split("\n");
      buffer = lines.pop() || ""; // Keep incomplete line in buffer

      for (const line of lines) {
        if (!line.startsWith("data: ")) continue;
        const jsonStr = line.slice(6);
        if (!jsonStr) continue;

        try {
          const event: StreamEvent = JSON.parse(jsonStr);

          switch (event.type) {
            case "text_delta":
              if (event.content) callbacks.onTextDelta(event.content);
              break;
            case "tool_start":
              if (event.tool_name && event.tool_use_id)
                callbacks.onToolStart(event.tool_name, event.tool_use_id);
              break;
            case "tool_result":
              if (event.tool_use_id)
                callbacks.onToolResult(event.tool_use_id, event.tool_name || "", event.result);
              break;
            case "done":
              callbacks.onDone();
              break;
            case "error":
              callbacks.onError(event.error || "Unknown error");
              break;
          }
        } catch {
          // Skip malformed JSON lines
        }
      }
    }
  } finally {
    reader.releaseLock();
  }
}
