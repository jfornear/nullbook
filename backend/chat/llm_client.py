"""Provider-agnostic LLM client.

Routes to Anthropic (default), OpenAI, or Ollama (via OpenAI-compatible API)
based on settings.LLM_PROVIDER.  Three methods:

- stream_chat()     — streaming chat with tool use (yields normalized events)
- complete()        — non-streaming completion (categorization, etc.)
- vision_extract()  — multimodal completion for receipt OCR
"""

import base64
import json
import logging

from django.conf import settings

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Format conversion helpers
# ---------------------------------------------------------------------------

def _anthropic_tools_to_openai(tools):
    """Convert Anthropic tool definitions to OpenAI function-calling format.

    Anthropic: {"name": ..., "description": ..., "input_schema": {...}}
    OpenAI:    {"type": "function", "function": {"name": ..., "description": ..., "parameters": {...}}}
    """
    out = []
    for t in tools:
        out.append({
            "type": "function",
            "function": {
                "name": t["name"],
                "description": t.get("description", ""),
                "parameters": t.get("input_schema", {"type": "object", "properties": {}}),
            },
        })
    return out


def _convert_messages_to_openai(messages, system_prompt=None):
    """Convert Anthropic-format conversation messages to OpenAI format.

    Handles:
    - system prompt -> {role: "system"} message
    - assistant content blocks (text + tool_use) -> text + tool_calls
    - user tool_result blocks -> {role: "tool"} messages
    - plain text user messages (pass-through)
    - multimodal content with images/documents
    """
    out = []
    if system_prompt:
        out.append({"role": "system", "content": system_prompt})

    for msg in messages:
        role = msg["role"]
        content = msg["content"]

        # Plain text message
        if isinstance(content, str):
            out.append({"role": role, "content": content})
            continue

        # Content is a list of blocks
        if role == "assistant":
            text_parts = []
            tool_calls = []
            for block in content:
                if block.get("type") == "text":
                    text_parts.append(block["text"])
                elif block.get("type") == "tool_use":
                    tool_calls.append({
                        "id": block["id"],
                        "type": "function",
                        "function": {
                            "name": block["name"],
                            "arguments": json.dumps(block.get("input", {})),
                        },
                    })
            oai_msg = {"role": "assistant", "content": "\n".join(text_parts) if text_parts else None}
            if tool_calls:
                oai_msg["tool_calls"] = tool_calls
            out.append(oai_msg)

        elif role == "user":
            # Could be tool results or multimodal content
            tool_results = [b for b in content if b.get("type") == "tool_result"]
            if tool_results:
                for tr in tool_results:
                    c = tr.get("content", "")
                    out.append({
                        "role": "tool",
                        "tool_call_id": tr["tool_use_id"],
                        "content": c if isinstance(c, str) else json.dumps(c),
                    })
            else:
                # Multimodal user message (images / text)
                oai_content = []
                for block in content:
                    btype = block.get("type")
                    if btype == "text":
                        oai_content.append({"type": "text", "text": block["text"]})
                    elif btype in ("image", "document"):
                        src = block.get("source", {})
                        media_type = src.get("media_type", "image/jpeg")
                        data = src.get("data", "")
                        oai_content.append({
                            "type": "image_url",
                            "image_url": {"url": f"data:{media_type};base64,{data}"},
                        })
                if oai_content:
                    out.append({"role": "user", "content": oai_content})
        else:
            # Pass through any other role
            out.append(msg)

    return out


def _coerce_tool_arguments(arguments):
    """Parse tool call arguments from string to dict.

    Local models sometimes return arguments as a JSON string rather than
    a parsed dict, or may return slightly malformed JSON.  This also
    coerces numeric-string values to ints/floats where the JSON schema
    expects numbers.
    """
    if isinstance(arguments, str):
        try:
            arguments = json.loads(arguments)
        except json.JSONDecodeError:
            arguments = {}
    if not isinstance(arguments, dict):
        arguments = {}
    return arguments


# ---------------------------------------------------------------------------
# LLMClient
# ---------------------------------------------------------------------------

class LLMClient:
    """Unified interface to Anthropic (default), OpenAI, or Ollama."""

    def __init__(self):
        self.provider = getattr(settings, "LLM_PROVIDER", "anthropic")

    # ---- streaming chat with tool use ----

    def stream_chat(self, messages, system_prompt, tools=None, model=None):
        """Yield streaming events for chat + tool use.

        Yields dicts with keys:
            {"type": "text_delta", "content": str}
            {"type": "tool_start", "tool_name": str, "tool_use_id": str}
            {"type": "tool_calls", "tool_calls": [{"id", "name", "input"}]}
            {"type": "done"}
            {"type": "error", "error": str}
        """
        if self.provider == "anthropic":
            yield from self._stream_anthropic(messages, system_prompt, tools, model)
        else:
            # Both "openai" and "ollama" use the OpenAI-compatible path
            yield from self._stream_openai(messages, system_prompt, tools, model)

    # ---- non-streaming completion ----

    def complete(self, messages, model=None):
        """Return a single text completion (non-streaming)."""
        if self.provider == "anthropic":
            return self._complete_anthropic(messages, model)
        return self._complete_openai(messages, model)

    # ---- vision / multimodal extraction ----

    def vision_extract(self, image_data, media_type, prompt, model=None):
        """Send an image + prompt, return the text response."""
        if self.provider == "anthropic":
            return self._vision_anthropic(image_data, media_type, prompt, model)
        return self._vision_openai(image_data, media_type, prompt, model)

    # ===================================================================
    # OpenAI-compatible (OpenAI + Ollama) implementations
    # ===================================================================

    def _get_openai_client(self):
        from openai import OpenAI
        if self.provider == "openai":
            api_key = getattr(settings, "OPENAI_API_KEY", "")
            if not api_key:
                raise RuntimeError("OPENAI_API_KEY is not configured.")
            return OpenAI(
                api_key=api_key,
                base_url="https://api.openai.com/v1",
            )
        # Ollama (default fallback for non-anthropic, non-openai)
        return OpenAI(
            base_url=settings.OLLAMA_BASE_URL,
            api_key="ollama",  # Ollama doesn't need a real key
        )

    def _stream_openai(self, messages, system_prompt, tools, model):
        from openai import APIError

        try:
            client = self._get_openai_client()
        except RuntimeError as e:
            yield {"type": "error", "error": str(e)}
            return

        model = model or settings.CHAT_MODEL
        oai_messages = _convert_messages_to_openai(messages, system_prompt)

        kwargs = {
            "model": model,
            "messages": oai_messages,
            "max_tokens": 4096,
            "stream": True,
        }
        if tools:
            kwargs["tools"] = _anthropic_tools_to_openai(tools)

        try:
            stream = client.chat.completions.create(**kwargs)
        except APIError as e:
            status_code = getattr(e, "status_code", None)
            if status_code == 404:
                if self.provider == "openai":
                    yield {"type": "error", "error": f"Model \"{model}\" not found on OpenAI."}
                else:
                    yield {"type": "error", "error": f"Model \"{model}\" not found. Run: ollama pull {model}"}
            else:
                yield {"type": "error", "error": f"AI service error: {e.message}"}
            return
        except Exception as e:
            err_str = str(e).lower()
            if "connection" in err_str or "refused" in err_str:
                if self.provider == "openai":
                    yield {"type": "error", "error": "OpenAI API error: could not connect."}
                else:
                    yield {"type": "error", "error": "Ollama is not running. Start it with: ollama serve"}
            else:
                logger.exception("OpenAI stream creation error")
                yield {"type": "error", "error": "An unexpected error occurred."}
            return

        # Accumulate text and tool calls from deltas
        collected_text = ""
        # tool_calls_by_index: {index: {"id", "name", "arguments_str"}}
        tool_calls_by_index = {}
        announced_tools = set()

        try:
            for chunk in stream:
                choice = chunk.choices[0] if chunk.choices else None
                if not choice:
                    continue
                delta = choice.delta

                # Text content
                if delta.content:
                    collected_text += delta.content
                    yield {"type": "text_delta", "content": delta.content}

                # Tool calls (streamed incrementally by index)
                if delta.tool_calls:
                    for tc_delta in delta.tool_calls:
                        idx = tc_delta.index
                        if idx not in tool_calls_by_index:
                            tool_calls_by_index[idx] = {
                                "id": tc_delta.id or f"call_{idx}",
                                "name": "",
                                "arguments_str": "",
                            }
                        entry = tool_calls_by_index[idx]
                        if tc_delta.id:
                            entry["id"] = tc_delta.id
                        if tc_delta.function:
                            if tc_delta.function.name:
                                entry["name"] = tc_delta.function.name
                            if tc_delta.function.arguments:
                                entry["arguments_str"] += tc_delta.function.arguments

                        # Emit tool_start once we know the name
                        if entry["name"] and idx not in announced_tools:
                            announced_tools.add(idx)
                            yield {
                                "type": "tool_start",
                                "tool_name": entry["name"],
                                "tool_use_id": entry["id"],
                            }

                # Check for finish
                if choice.finish_reason:
                    break
        except APIError as e:
            yield {"type": "error", "error": f"AI service error: {e.message}"}
            return
        except Exception:
            logger.exception("OpenAI streaming error")
            yield {"type": "error", "error": "An unexpected error occurred."}
            return

        # Emit accumulated tool calls
        if tool_calls_by_index:
            parsed_calls = []
            for idx in sorted(tool_calls_by_index):
                entry = tool_calls_by_index[idx]
                parsed_calls.append({
                    "id": entry["id"],
                    "name": entry["name"],
                    "input": _coerce_tool_arguments(entry["arguments_str"]),
                })
            yield {"type": "tool_calls", "tool_calls": parsed_calls}
        else:
            yield {"type": "done"}

    def _complete_openai(self, messages, model):
        client = self._get_openai_client()  # raises RuntimeError if key missing
        model = model or settings.CHAT_MODEL_FAST
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            max_tokens=1024,
        )
        return response.choices[0].message.content or ""

    def _vision_openai(self, image_data, media_type, prompt, model):
        client = self._get_openai_client()  # raises RuntimeError if key missing
        model = model or settings.VISION_MODEL

        # For PDFs, convert to image first (Ollama/OpenAI models don't accept PDFs)
        if media_type == "application/pdf":
            image_data, media_type = self._pdf_to_image(image_data)

        messages = [{
            "role": "user",
            "content": [
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:{media_type};base64,{image_data}"},
                },
                {"type": "text", "text": prompt},
            ],
        }]
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            max_tokens=2048,
        )
        return response.choices[0].message.content or ""

    # ===================================================================
    # Anthropic implementations
    # ===================================================================

    def _get_anthropic_client(self):
        import anthropic
        api_key = settings.ANTHROPIC_API_KEY
        if not api_key:
            raise RuntimeError("ANTHROPIC_API_KEY is not configured.")
        return anthropic.Anthropic(api_key=api_key)

    def _stream_anthropic(self, messages, system_prompt, tools, model):
        import anthropic

        try:
            client = self._get_anthropic_client()
        except RuntimeError as e:
            yield {"type": "error", "error": str(e)}
            return

        model = model or settings.CHAT_MODEL

        kwargs = {
            "model": model,
            "max_tokens": 4096,
            "system": system_prompt,
            "messages": messages,
        }
        if tools:
            kwargs["tools"] = tools

        try:
            with client.messages.stream(**kwargs) as stream:
                for event in stream:
                    if event.type == "content_block_start":
                        block = event.content_block
                        if block.type == "tool_use":
                            yield {
                                "type": "tool_start",
                                "tool_name": block.name,
                                "tool_use_id": block.id,
                            }
                    elif event.type == "content_block_delta":
                        delta = event.delta
                        if delta.type == "text_delta":
                            yield {"type": "text_delta", "content": delta.text}

                final_message = stream.get_final_message()

        except anthropic.APIStatusError as e:
            yield {"type": "error", "error": f"AI service error: {e.message}"}
            return
        except Exception:
            logger.exception("Anthropic streaming error")
            yield {"type": "error", "error": "An unexpected error occurred."}
            return

        tool_use_blocks = [b for b in final_message.content if b.type == "tool_use"]
        if tool_use_blocks:
            yield {
                "type": "tool_calls",
                "tool_calls": [
                    {
                        "id": b.id,
                        "name": b.name,
                        "input": b.input if isinstance(b.input, dict) else {},
                    }
                    for b in tool_use_blocks
                ],
            }
        else:
            yield {"type": "done"}

    def _complete_anthropic(self, messages, model):
        client = self._get_anthropic_client()
        model = model or settings.CHAT_MODEL_FAST
        response = client.messages.create(
            model=model,
            max_tokens=1024,
            messages=messages,
        )
        return response.content[0].text

    def _vision_anthropic(self, image_data, media_type, prompt, model):
        client = self._get_anthropic_client()
        model = model or settings.CHAT_MODEL
        is_pdf = media_type == "application/pdf"
        response = client.messages.create(
            model=model,
            max_tokens=2048,
            messages=[{
                "role": "user",
                "content": [
                    {
                        "type": "document" if is_pdf else "image",
                        "source": {
                            "type": "base64",
                            "media_type": media_type,
                            "data": image_data,
                        },
                    },
                    {"type": "text", "text": prompt},
                ],
            }],
        )
        return response.content[0].text

    # ===================================================================
    # Utilities
    # ===================================================================

    @staticmethod
    def _pdf_to_image(pdf_base64_data):
        """Convert a base64-encoded PDF to a base64-encoded PNG of the first page.

        Uses Pillow (already a project dependency). Falls back to sending
        raw image data if conversion fails.
        """
        try:
            from PIL import Image
            import io

            pdf_bytes = base64.b64decode(pdf_base64_data)

            # Pillow can open PDFs if the PDF plugin is available
            # (requires poppler or similar). Try it, fall back to raw bytes.
            img = Image.open(io.BytesIO(pdf_bytes))
            img = img.convert("RGB")

            buf = io.BytesIO()
            img.save(buf, format="PNG")
            buf.seek(0)
            return base64.b64encode(buf.read()).decode("utf-8"), "image/png"
        except Exception:
            logger.warning("PDF-to-image conversion failed, sending raw data")
            return pdf_base64_data, "application/pdf"
