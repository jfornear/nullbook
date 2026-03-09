"""SSE streaming endpoint for LLM-powered chat."""

import base64
import json
import logging

from django.http import StreamingHttpResponse
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from .llm_client import LLMClient
from .models import Conversation, Message
from .tools import TOOL_DEFINITIONS, execute_tool

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are nullbook, an AI personal finance agent. You have access to the user's financial data and can take actions on their behalf through tools.

Guidelines:
- Be concise and helpful. Use markdown formatting for clarity.
- IMPORTANT: Do not use emojis or emoticons anywhere in your responses. Use plain text only.
- When the user asks about their finances, use the appropriate tool to fetch real data.
- Present numbers formatted as currency where appropriate.
- If you need to look up multiple things, call the tools you need.
- Don't make up financial data — always use tools to get real information.
- When showing data, briefly summarize the key insights rather than just repeating raw numbers.
- You can use tables, lists, and bold text to make responses scannable.

Bank & Account Syncing:
- Use link_bank_account to help users connect their bank via Plaid.
- Use sync_accounts to trigger manual bank transaction syncing.
- Proactively suggest connecting a bank if the user has no accounts.

Email & Receipt Scanning:
- Use connect_email to set up IMAP email scanning for receipts.
- Use scan_email_now to trigger an immediate email scan.
- Use get_email_receipts to show receipts found via email.
- When a user uploads a receipt image, describe what you see and let them know it's being processed.
- Use create_expense_from_receipt to turn processed receipts into tax deductions.

Subscriptions:
- Use get_subscriptions to show detected recurring charges.
- Use get_subscription_spending for cost summaries.
- Use cancel_subscription to help cancel subscriptions (always show draft first, send only with confirmation).
- Use track_cancellation to monitor pending cancellations.
- Proactively mention high-cost or unused subscriptions.

Tax Preparation:
- Use prepare_tax_filing for a guided tax workflow.
- Use generate_schedule_c for self-employment summaries.
- Use find_missed_deductions to scan for unclaimed deductions.
- Use export_tax_summary to generate exportable tax summaries.
- Use estimate_taxes for detailed federal tax estimates.
- Use compare_filing_statuses to find the optimal filing status.
- Always disclaim: these are estimates only — consult a tax professional for official filing.

Portfolio:
- Use get_portfolio_performance for market values and unrealized gains/losses.

Alerts:
- Use get_alerts to show the user's financial alerts and notifications.
- Mention relevant alerts proactively when they exist.

Action Safety:
- For destructive actions (cancellations, sending emails), always show a preview first and require explicit confirmation.
- Never auto-cancel subscriptions or send emails without user approval.

Proactive Behavior:
- When showing spending data, suggest specific ways to save (e.g., "Your dining spending is up 40% — want me to find subscription-free alternatives?").
- When showing subscriptions, flag ones with recent price increases or that seem unused (no charges in 60+ days).
- When tax deadlines are approaching (April 15, June 15, September 15, January 15), proactively mention tax prep.
- After importing transactions, offer to categorize them and scan for deductions.
- When the portfolio drops significantly, provide context about market conditions rather than causing panic.
- If the user has unread alerts, briefly mention them at the start of conversation.
- When the user first interacts and has no data, warmly guide them through onboarding: connecting a bank, importing transactions, or setting up email scanning."""

def _build_context(user):
    """Build dynamic financial context to prepend to the system prompt."""
    from datetime import timedelta
    from decimal import Decimal

    from django.db.models import Sum
    from django.utils import timezone

    from accounts.models import Account
    from core.models import Alert
    from transactions.models import Budget, Subscription, Transaction

    parts = []
    now = timezone.now()

    # Unread alerts
    unread_alerts = Alert.objects.filter(user=user, is_read=False)
    unread_count = unread_alerts.count()
    if unread_count > 0:
        urgent = unread_alerts.filter(severity="urgent").first()
        parts.append(f"The user has {unread_count} unread alert(s).")
        if urgent:
            parts.append(f"Most urgent: {urgent.title} — {urgent.message}")

    # Budget progress (single query for all category spending)
    budgets = list(Budget.objects.filter(user=user, is_active=True).select_related("category"))
    if budgets:
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        cat_spending = dict(
            Transaction.objects.filter(
                user=user, transaction_type="expense", date__gte=month_start.date()
            ).values("category_id").annotate(total=Sum("amount")).values_list("category_id", "total")
        )
        total_spending = sum(cat_spending.values(), Decimal("0"))

        budget_lines = []
        for b in budgets:
            spent = cat_spending.get(b.category_id, Decimal("0")) if b.category_id else total_spending
            pct = (spent / b.amount * 100) if b.amount else 0
            cat = b.category.name if b.category else "Total"
            budget_lines.append(f"  {cat}: ${spent:.0f} / ${b.amount:.0f} ({pct:.0f}%)")
        parts.append("Current budget progress:\n" + "\n".join(budget_lines))

    # Upcoming subscriptions (next 3 days)
    three_days = now.date() + timedelta(days=3)
    upcoming_subs = Subscription.objects.filter(
        user=user, status="active",
        next_expected__lte=three_days, next_expected__gte=now.date()
    )
    if upcoming_subs.exists():
        sub_names = [f"{s.merchant} (${s.amount})" for s in upcoming_subs[:5]]
        parts.append(f"Upcoming subscription charges: {', '.join(sub_names)}")

    # Net worth
    accounts = Account.objects.filter(user=user)
    if accounts.exists():
        net_worth = sum(a.balance for a in accounts)
        parts.append(f"Current net worth: ${net_worth:,.2f}")

    if not parts:
        return ""

    return "\n\nCurrent user context (real-time data):\n" + "\n".join(parts) + "\n\nIf this is the first message in a conversation and the user sends a greeting or general question, briefly mention any urgent alerts or notable budget status before answering."


def _sse_event(event_type, data):
    """Format a Server-Sent Event."""
    payload = json.dumps({"type": event_type, **data})
    return f"data: {payload}\n\n"


def _build_messages(conversation):
    """Build the messages list from conversation history.

    Stores in Anthropic-style block format internally (tool_use / tool_result).
    The LLMClient converts to OpenAI format when needed.
    """
    messages = []
    # Limit to most recent messages to prevent unbounded memory/token usage
    recent = list(conversation.messages.order_by("-created_at")[:100])
    recent.reverse()
    for msg in recent:
        if msg.role == "user":
            messages.append({"role": "user", "content": msg.content})
        elif msg.role == "assistant":
            # Reconstruct assistant message with tool calls if present
            content_blocks = []
            if msg.content:
                content_blocks.append({"type": "text", "text": msg.content})
            for tc in (msg.tool_calls or []):
                content_blocks.append({
                    "type": "tool_use",
                    "id": tc["id"],
                    "name": tc["name"],
                    "input": tc["input"],
                })
            if content_blocks:
                messages.append({"role": "assistant", "content": content_blocks})

            # Add tool results as user messages
            for tr in (msg.tool_results or []):
                messages.append({
                    "role": "user",
                    "content": [{
                        "type": "tool_result",
                        "tool_use_id": tr["tool_use_id"],
                        "content": json.dumps(tr["content"]),
                    }],
                })
    return messages


def _stream_response(conversation, user, image_file=None):
    """Generator that streams SSE events from the configured LLM provider."""
    llm = LLMClient()
    messages = _build_messages(conversation)
    system_prompt = SYSTEM_PROMPT + _build_context(user)

    # If there's an attached file, add it to the last user message
    if image_file and messages and messages[-1]["role"] == "user":
        file_data = base64.standard_b64encode(image_file.read()).decode("utf-8")
        content_type = getattr(image_file, "content_type", "image/jpeg") or "image/jpeg"
        is_pdf = content_type == "application/pdf"
        # Replace the last user message with multimodal content
        last_text = messages[-1]["content"]
        if isinstance(last_text, str):
            messages[-1]["content"] = [
                {
                    "type": "document" if is_pdf else "image",
                    "source": {
                        "type": "base64",
                        "media_type": content_type,
                        "data": file_data,
                    },
                },
                {"type": "text", "text": last_text},
            ]

    collected_text = ""
    collected_tool_calls = []
    collected_tool_results = []
    had_error = False

    # Tool use loop: keep calling the LLM until it stops requesting tools
    max_iterations = 10
    for iteration in range(max_iterations):
        current_text = ""
        current_tool_calls = []

        for event in llm.stream_chat(messages, system_prompt, tools=TOOL_DEFINITIONS):
            etype = event["type"]

            if etype == "text_delta":
                current_text += event["content"]
                collected_text += event["content"]
                yield _sse_event("text_delta", {"content": event["content"]})

            elif etype == "tool_start":
                yield _sse_event("tool_start", {
                    "tool_name": event["tool_name"],
                    "tool_use_id": event["tool_use_id"],
                })

            elif etype == "tool_calls":
                current_tool_calls = event["tool_calls"]

            elif etype == "error":
                yield _sse_event("error", {"error": event["error"]})
                had_error = True
                break

            elif etype == "done":
                pass

        if had_error:
            break

        if not current_tool_calls:
            # No tools requested — we're done
            break

        # Record tool calls
        for tc in current_tool_calls:
            collected_tool_calls.append({
                "id": tc["id"],
                "name": tc["name"],
                "input": tc["input"],
            })

        # Build assistant message for conversation context
        assistant_content = []
        if current_text:
            assistant_content.append({"type": "text", "text": current_text})
        for tc in current_tool_calls:
            assistant_content.append({
                "type": "tool_use",
                "id": tc["id"],
                "name": tc["name"],
                "input": tc["input"],
            })
        messages.append({"role": "assistant", "content": assistant_content})

        # Execute tools and feed results back
        tool_results_content = []
        for tc in current_tool_calls:
            result = execute_tool(tc["name"], tc["input"], user)

            tool_results_content.append({
                "type": "tool_result",
                "tool_use_id": tc["id"],
                "content": json.dumps(result),
            })

            collected_tool_results.append({
                "tool_use_id": tc["id"],
                "content": result,
                "component_type": result.get("component_type"),
            })

            yield _sse_event("tool_result", {
                "tool_use_id": tc["id"],
                "tool_name": tc["name"],
                "result": result,
            })

        messages.append({"role": "user", "content": tool_results_content})
    else:
        # Exceeded max iterations
        had_error = True
        yield _sse_event("error", {"error": "Too many tool calls. Please try a simpler question."})

    # Save the assistant message (skip if API failed with no content)
    if collected_text or collected_tool_calls:
        Message.objects.create(
            conversation=conversation,
            role="assistant",
            content=collected_text,
            tool_calls=collected_tool_calls,
            tool_results=collected_tool_results,
        )

    if not had_error:
        yield _sse_event("done", {})


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def stream_chat(request, conversation_id):
    """SSE endpoint: saves user message, streams LLM response with tool calls.

    Accepts JSON or multipart form data (when an image is attached).
    """
    try:
        conversation = Conversation.objects.get(
            id=conversation_id, user=request.user
        )
    except Conversation.DoesNotExist:
        return Response(
            {"detail": "Conversation not found."},
            status=status.HTTP_404_NOT_FOUND,
        )

    content = request.data.get("content", "").strip()
    if not content:
        return Response(
            {"detail": "Message content is required."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    image_file = request.FILES.get("image")

    # If image uploaded, create a Receipt and kick off OCR
    receipt = None
    if image_file:
        from taxes.models import Receipt
        from taxes.tasks import process_receipt_task

        receipt = Receipt.objects.create(
            user=request.user,
            image=image_file,
        )
        process_receipt_task.delay(receipt.id)

    # Save user message
    Message.objects.create(
        conversation=conversation,
        role="user",
        content=content,
    )

    # Auto-title from first user message immediately so sidebar updates fast
    if not conversation.title:
        conversation.title = content[:100]
        conversation.save(update_fields=["title"])

    # Re-open the image file for LLM vision (seek back to start if needed)
    image_for_vision = None
    if image_file:
        image_file.seek(0)
        image_for_vision = image_file

    response = StreamingHttpResponse(
        _stream_response(conversation, request.user, image_file=image_for_vision),
        content_type="text/event-stream",
    )
    response["Cache-Control"] = "no-cache"
    response["X-Accel-Buffering"] = "no"
    return response
