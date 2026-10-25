"""Unified QA prompt for LongMemEval-s, shared by all baselines.

Every baseline answers with this prompt instead of its own answer template, so that
score differences come from memory construction and retrieval, not from answer style.

Usage:

    from common.qa_prompts.qa_longmemeval import (
        build_messages, ANSWER_TEMPERATURE, ANSWER_MAX_TOKENS)

    messages = build_messages(memory_block=rendered_retrieval,
                              question_date=q["question_date"],
                              question=q["question"],
                              question_type=q["question_type"],
                              profile_block=None)

Rendering notes for baselines:
  * If retrieved memory units carry timestamps, render them into `memory_block`;ß
    rule 2 relies on them.
  * `profile_block` is for persistent user profiles / knowledge kept outside
    per-query retrieval (e.g. MemoryOS). Anything retrieved for the current query
    goes into `memory_block`.
"""

from __future__ import annotations

from string import Template
from typing import List, Optional

PROMPT_VERSION = "longmemeval/unified-v3-pref"

# The LongMemEval-s value is `single-session-preference` (30 of 500 questions);
# the underscore spelling is accepted as well.
PREFERENCE_TYPES = frozenset({
    "single-session-preference", "single_session_preference"
})


SYSTEM_PROMPT = (
    "You are a helpful assistant with a long-term memory of your past "
    "conversations with the user. Answer the user's question based on your "
    "memories.\n"
    "\n"
    "Follow these rules:\n"
    "1. Be concise and specific. For dates use the format \"15 July 2023\"; "
    "for durations answer in years/months/days.\n"
    "2. Time: reason from the timestamps attached to your memories and from "
    "the current date given with the question. Resolve relative expressions "
    "(\"last year\", \"how long ago\") against the current date, not against "
    "when the conversation happened.\n"
    "3. Conflicts: if memories disagree because something changed over time, "
    "trust the most recent memory, unless the question asks about an earlier "
    "point in time.\n"
    "4. The needed evidence may be scattered across several conversations; "
    "combine related memories before answering.\n"
    "5. Do not make up information. If the needed information does not appear "
    "in your memories, say that the information is not available."
)

# Preference questions: rules 1-4 only.
SYSTEM_PROMPT_PREFERENCE = SYSTEM_PROMPT.split("\n5. ")[0]

# string.Template ($-substitution) instead of str.format: memory text often
# contains braces / JSON fragments.
USER_PROMPT_TEMPLATE = Template(
    "<MEMORY>\n"
    "$memory_block\n"
    "$profile_section"
    "\n"
    "Current date: $question_date\n"
    "Question: $question\n"
    "$tail"
)

# Omitted entirely (no empty header) when `profile_block` is empty.
PROFILE_SECTION_TEMPLATE = Template(
    "\n"
    "<USER PROFILE>\n"
    "$profile_block\n"
)

EMPTY_MEMORY_PLACEHOLDER = "(no relevant memory retrieved)"

# Closing instruction for all non-preference question types.
TAIL_DEFAULT = "Answer concisely, providing only the answer content."

# Closing instruction for preference questions: the answer is judged on whether it
# reflects the user's preferences, so it is not forced into a short span.
TAIL_PREFERENCE = (
    "Read all sentences carefully and extract the information that may be relevant "
    "to the question step by step. \n\n"
    "Your answer should fully consider the user's preferences."
)


def is_preference(question_type) -> bool:
    return str(question_type or "").strip().lower() in PREFERENCE_TYPES


def build_user_prompt(memory_block: str, question_date: str, question: str,
                      question_type: str = "",
                      profile_block: Optional[str] = None) -> str:
    profile_section = ""
    if profile_block and profile_block.strip():
        profile_section = PROFILE_SECTION_TEMPLATE.substitute(
            profile_block=profile_block.strip())
    return USER_PROMPT_TEMPLATE.substitute(
        memory_block=(memory_block.strip() if memory_block and memory_block.strip()
                      else EMPTY_MEMORY_PLACEHOLDER),
        profile_section=profile_section,
        question_date=str(question_date or "").strip(),
        question=question.strip(),
        tail=TAIL_PREFERENCE if is_preference(question_type) else TAIL_DEFAULT,
    )


def build_messages(memory_block: str, question_date: str, question: str,
                   question_type: str = "",
                   profile_block: Optional[str] = None) -> List[dict]:
    """Return [{"role": "system", ...}, {"role": "user", ...}] for chat completion."""
    sys_prompt = SYSTEM_PROMPT_PREFERENCE if is_preference(question_type) else SYSTEM_PROMPT
    return [
        {"role": "system", "content": sys_prompt},
        {"role": "user", "content": build_user_prompt(
            memory_block, question_date, question, question_type, profile_block)},
    ]


# Sampling parameters, identical across baselines.
ANSWER_TEMPERATURE = 0.0
ANSWER_MAX_TOKENS = 512     # preference questions need paragraph-length answers


if __name__ == "__main__":                       # print an example prompt
    msgs = build_messages(
        memory_block=("[2023-05-20 Sat] user: I finally adopted the corgi from "
                      "the shelter — named him Biscuit.\n"
                      "[2023-07-02 Sun] user: Biscuit's first vet visit went "
                      "fine, he weighs 11 kg now."),
        question_date="2023-08-10",
        question="How long ago did I adopt Biscuit?",
        question_type="multi-session",
        profile_block="Dog owner (corgi named Biscuit); prefers metric units.")
    for m in msgs:
        print(f"----- {m['role']} -----\n{m['content']}\n")
