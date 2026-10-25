"""Unified QA prompt for MINT-Eval, shared by all baselines and all four subdomains
(multi-turn dialogue, state tracking, GitHub commits, wiki revisions).

Each MINT-Eval sample is a time-ordered stream of steps, ingested as `[step i]`
prefixed units. Many questions ask about history, ordering, counting or
"N steps back", so the system prompt fixes the meaning of the step labels: counting
follows the `[step i]` labels, not the order in which retrieved memories are listed.

Usage:

    from common.qa_prompts.qa_mint_eval import (
        build_messages, ANSWER_TEMPERATURE, ANSWER_MAX_TOKENS)

    messages = build_messages(memory_block=rendered_retrieval,
                              question=q["question"],
                              question_type=q.get("question_type"))

A baseline decides what to retrieve and how to render it, but must keep the
`[step i]` prefix in `memory_block`; ordering and N-steps-back questions are
unanswerable without it.
"""

from __future__ import annotations

from string import Template
from typing import List, Optional

PROMPT_VERSION = "mint_eval/unified-v1"

SYSTEM_PROMPT = (
    "You are a helpful assistant with a long-term memory of a stream of "
    "time-ordered records you have observed (conversation steps, state updates, "
    "commits, or document revisions). Answer the user's question based on your "
    "memories.\n"
    "\n"
    "Follow these rules:\n"
    "1. Be concise and specific. Answer with the requested value only — no "
    "explanation, no restating of the question.\n"
    "2. Every memory is labelled with its position in the stream as "
    "\"[step i]\", optionally followed by a timestamp. Counting questions "
    "(\"N steps back\", \"the step before X\") are answered from those step "
    "labels, NOT from the order in which the memories are listed below.\n"
    "3. The stream evolves: a later step supersedes an earlier one when the "
    "same thing changed, unless the question explicitly asks about an earlier "
    "point in the history.\n"
    "4. The evidence may be spread over several steps; combine them before "
    "answering.\n"
    "5. Do not make up information. If the needed information does not appear "
    "in your memories, say that the information is not available."
)

USER_PROMPT_TEMPLATE = Template(
    "<MEMORY>\n"
    "$memory_block\n"
    "$profile_section"
    "\n"
    "Question: $question\n"
    "$tail"
)

# Omitted entirely (no empty header) when `profile_block` is empty.
PROFILE_SECTION_TEMPLATE = Template(
    "\n"
    "<SUMMARY>\n"
    "$profile_block\n"
)

EMPTY_MEMORY_PLACEHOLDER = "(no relevant memory retrieved)"

TAIL_DEFAULT = "Answer concisely, providing only the answer content."


def build_user_prompt(memory_block: str, question: str, question_type: str = "",
                      profile_block: Optional[str] = None) -> str:
    profile_section = ""
    if profile_block and profile_block.strip():
        profile_section = PROFILE_SECTION_TEMPLATE.substitute(
            profile_block=profile_block.strip())
    return USER_PROMPT_TEMPLATE.substitute(
        memory_block=(memory_block.strip() if memory_block and memory_block.strip()
                      else EMPTY_MEMORY_PLACEHOLDER),
        profile_section=profile_section,
        question=str(question).strip(),
        tail=TAIL_DEFAULT,
    )


def build_messages(memory_block: str, question: str, question_type: str = "",
                   profile_block: Optional[str] = None) -> List[dict]:
    """Return [{"role": "system", ...}, {"role": "user", ...}] for chat completion."""
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": build_user_prompt(
            memory_block, question, question_type, profile_block)},
    ]


# Sampling parameters, identical across baselines.
ANSWER_TEMPERATURE = 0.0
ANSWER_MAX_TOKENS = 256     # values or short lists


if __name__ == "__main__":                       # print an example prompt
    for m in build_messages(
            memory_block="[step 12] (2024-03-01) status: open, assignee: Dana\n"
                         "[step 17] (2024-03-04) status: closed, assignee: Dana",
            question="What was the status two steps after step 12?"):
        print(f"----- {m['role']} -----\n{m['content']}\n")
