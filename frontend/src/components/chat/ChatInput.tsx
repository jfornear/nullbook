import { useRef, useEffect, KeyboardEvent, useState, DragEvent } from "react";
import { ArrowUp, FileText, Paperclip, X } from "lucide-react";
import { Button } from "@/components/ui/button";

interface ChatInputProps {
  onSend: (content: string, image?: File) => void;
  disabled?: boolean;
  placeholder?: string;
  autoFocus?: boolean;
}

const ACCEPTED_TYPES = ".jpg,.jpeg,.png,.webp,.gif,.pdf";
const ACCEPTED_MIME = ["image/jpeg", "image/png", "image/webp", "image/gif", "application/pdf"];

export function ChatInput({
  onSend,
  disabled,
  placeholder = "Ask anything about your finances...",
  autoFocus = false,
}: ChatInputProps) {
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [value, setValue] = useState("");
  const [attachedImage, setAttachedImage] = useState<File | null>(null);
  const [imagePreview, setImagePreview] = useState<string | null>(null);
  const [isDragging, setIsDragging] = useState(false);

  useEffect(() => {
    if (autoFocus && textareaRef.current) {
      textareaRef.current.focus();
    }
  }, [autoFocus]);

  useEffect(() => {
    const ta = textareaRef.current;
    if (ta) {
      ta.style.height = "auto";
      ta.style.height = Math.min(ta.scrollHeight, 200) + "px";
    }
  }, [value]);

  // Global "/" shortcut to focus
  useEffect(() => {
    function handleKeyDown(e: globalThis.KeyboardEvent) {
      if (
        e.key === "/" &&
        !e.metaKey &&
        !e.ctrlKey &&
        document.activeElement?.tagName !== "INPUT" &&
        document.activeElement?.tagName !== "TEXTAREA"
      ) {
        e.preventDefault();
        textareaRef.current?.focus();
      }
    }
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, []);

  // Clean up preview URL on unmount
  useEffect(() => {
    return () => {
      if (imagePreview) URL.revokeObjectURL(imagePreview);
    };
  }, [imagePreview]);

  function attachFile(file: File) {
    if (!ACCEPTED_MIME.includes(file.type)) return;
    if (imagePreview) URL.revokeObjectURL(imagePreview);
    setAttachedImage(file);
    setImagePreview(URL.createObjectURL(file));
  }

  function removeImage() {
    setAttachedImage(null);
    if (imagePreview) URL.revokeObjectURL(imagePreview);
    setImagePreview(null);
    if (fileInputRef.current) fileInputRef.current.value = "";
  }

  function handleSend() {
    const trimmed = value.trim();
    if ((!trimmed && !attachedImage) || disabled) return;
    onSend(trimmed || "Here's a receipt image.", attachedImage || undefined);
    setValue("");
    removeImage();
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
    }
  }

  function handleKeyDown(e: KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  }

  function handleDragOver(e: DragEvent) {
    e.preventDefault();
    setIsDragging(true);
  }

  function handleDragLeave(e: DragEvent) {
    e.preventDefault();
    setIsDragging(false);
  }

  function handleDrop(e: DragEvent) {
    e.preventDefault();
    setIsDragging(false);
    const file = e.dataTransfer.files?.[0];
    if (file) attachFile(file);
  }

  return (
    <div
      className={`rounded-2xl border bg-muted/50 p-4 shadow-sm transition-colors focus-within:border-foreground/20 ${
        isDragging ? "border-primary border-dashed bg-primary/5" : ""
      }`}
      onDragOver={handleDragOver}
      onDragEnter={handleDragOver}
      onDragLeave={handleDragLeave}
      onDrop={handleDrop}
    >
      {/* Attachment preview */}
      {attachedImage && (
        <div className="mb-2 flex items-start gap-2">
          <div className="relative">
            {attachedImage.type === "application/pdf" ? (
              <div className="flex h-16 w-16 items-center justify-center rounded-lg border bg-muted">
                <FileText className="h-6 w-6 text-muted-foreground" />
              </div>
            ) : (
              <img
                src={imagePreview!}
                alt="Attached"
                className="h-16 w-16 rounded-lg border object-cover"
              />
            )}
            <button
              type="button"
              onClick={removeImage}
              className="absolute -right-1 -top-1 flex h-4 w-4 items-center justify-center rounded-full bg-destructive text-destructive-foreground"
            >
              <X className="h-2.5 w-2.5" />
            </button>
          </div>
          <span className="text-xs text-muted-foreground pt-1">{attachedImage.name}</span>
        </div>
      )}

      <textarea
        ref={textareaRef}
        data-chat-input
        value={value}
        onChange={(e) => setValue(e.target.value)}
        onKeyDown={handleKeyDown}
        placeholder={placeholder}
        aria-label="Chat message"
        disabled={disabled}
        rows={1}
        className="w-full resize-none bg-transparent px-1 py-1 text-sm outline-none placeholder:text-muted-foreground disabled:opacity-50"
      />
      <div className="flex items-center justify-between pt-2">
        <div>
          <input
            ref={fileInputRef}
            type="file"
            accept={ACCEPTED_TYPES}
            className="hidden"
            onChange={(e) => {
              const file = e.target.files?.[0];
              if (file) attachFile(file);
            }}
          />
          <Button
            variant="ghost"
            size="icon"
            className="h-8 w-8 rounded-lg"
            onClick={() => fileInputRef.current?.click()}
            disabled={disabled}
          >
            <Paperclip className="h-4 w-4" />
            <span className="sr-only">Attach file</span>
          </Button>
        </div>
        <Button
          size="icon"
          className="h-8 w-8 rounded-lg"
          onClick={handleSend}
          disabled={disabled || (!value.trim() && !attachedImage)}
        >
          <ArrowUp className="h-4 w-4" />
          <span className="sr-only">Send</span>
        </Button>
      </div>
    </div>
  );
}
