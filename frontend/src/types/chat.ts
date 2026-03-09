export interface Conversation {
  id: string;
  title: string;
  is_pinned: boolean;
  is_archived: boolean;
  message_count: number;
  last_message: {
    role: "user" | "assistant";
    content: string;
    created_at: string;
  } | null;
  created_at: string;
  updated_at: string;
}

export interface Message {
  id: string;
  conversation: string;
  role: "user" | "assistant";
  content: string;
  tool_calls: ToolCall[];
  tool_results: ToolResult[];
  created_at: string;
}

export interface ConversationDetail {
  id: string;
  title: string;
  is_pinned: boolean;
  is_archived: boolean;
  messages: Message[];
  created_at: string;
  updated_at: string;
}

export interface ToolCall {
  id: string;
  name: string;
  input: Record<string, unknown>;
}

export interface ToolResult {
  tool_use_id: string;
  content: unknown;
  component_type?: string;
}

export interface SendMessageResponse {
  user_message: Message;
  assistant_message: Message;
}

export interface StreamEvent {
  type: "text_delta" | "tool_start" | "tool_result" | "done" | "error";
  content?: string;
  tool_name?: string;
  tool_use_id?: string;
  result?: Record<string, unknown>;
  error?: string;
}

export interface Receipt {
  id: number;
  merchant: string;
  date: string | null;
  total_amount: string | null;
  subtotal: string | null;
  tax_amount: string | null;
  tip_amount: string | null;
  currency: string;
  payment_method: string;
  category: string;
  status: "pending" | "processing" | "completed" | "failed";
  image_url: string | null;
  line_items: ReceiptLineItem[];
  created_at: string;
}

export interface ReceiptLineItem {
  id: number;
  description: string;
  quantity: string;
  unit_price: string | null;
  total_price: string;
  category: string;
}
