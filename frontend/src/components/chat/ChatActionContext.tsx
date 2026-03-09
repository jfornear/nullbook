import { createContext, useContext, type ReactNode } from "react";

interface ChatActionContextValue {
  sendMessage: (content: string) => void;
}

const ChatActionContext = createContext<ChatActionContextValue | null>(null);

export function ChatActionProvider({
  children,
  sendMessage,
}: {
  children: ReactNode;
  sendMessage: (content: string) => void;
}) {
  return (
    <ChatActionContext.Provider value={{ sendMessage }}>{children}</ChatActionContext.Provider>
  );
}

export function useChatAction(): ChatActionContextValue | null {
  return useContext(ChatActionContext);
}
