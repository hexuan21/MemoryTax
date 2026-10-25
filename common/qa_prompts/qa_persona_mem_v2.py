"""Unified QA prompt for PersonaMem-v2 (128k), shared by all baselines.

PersonaMem-v2 is 4-way multiple choice and is scored by the chosen letter. A single
prompt and output contract (one letter) keeps parsing identical across baselines, so
"could not parse" is never mixed into "wrong".

Usage:

    from common.qa_prompts.qa_persona_mem_v2 import (
        build_messages, parse_answer, shuffle_options,
        ANSWER_TEMPERATURE, ANSWER_MAX_TOKENS)

    options, gold = shuffle_options(row["correct_answer"],
                                    json.loads(row["incorrect_answers"]),
                                    rng)          # rng seeded per question
    messages = build_messages(question=user_question,
                              options=options,
                              memory_block=rendered_retrieval,
                              profile_block=None)
    pred = parse_answer(raw_output, options)      # 'A'..'D', or '' if unparsable

Data notes:
  * `user_query` cells are Python dict literals; decode with `ast.literal_eval`,
    not `json.loads` after quote replacement (that breaks on "day's" / "don't").
  * The first system message of each chat history (the persona JSON) is part of
    the official protocol and is kept.
  * Shuffle options with a per-question seed; otherwise the correct answer is
    always last.
  * Count unparsable outputs (`''`) separately; in our evaluation they are sent
    to the LLM judge instead of being scored as wrong.
"""

from __future__ import annotations

from string import Template
from typing import List, Optional, Sequence, Tuple

PROMPT_VERSION = "persona_mem_v2/unified-v3-official-sys-strict"

LETTERS = ("A", "B", "C", "D")


# Aligned with the system prompt of the official PersonaMem-v2 RAG baseline (two
# system messages there, merged into one here). "The following ... excerpts" refers
# to the <MEMORY> section of the user prompt. The one-letter output contract is
# stated at the end of the user prompt.
SYSTEM_PROMPT = (
    "You are a helpful assistant that provides personalized responses "
    "based on the user's preferences in conversation history.\n"
    "\n"
    "The following are relevant excerpts from your conversation history "
    "with this user. Use them to personalize your response."
)

# string.Template ($-substitution) instead of str.format: memory text often
# contains braces / JSON fragments.
USER_PROMPT_TEMPLATE = Template(
    "<MEMORY>\n"
    "$memory_block\n"
    "$profile_section"
    "\n"
    "<QUESTION>\n"
    "$question\n"
    "\n"
    "<CANDIDATE RESPONSES>\n"
    "$options_block\n"
    "\n"
    "Which candidate response best fits this user? Answer with one letter "
    "(A, B, C or D) and nothing else. No explanation."
)

# Omitted entirely (no empty header) when `profile_block` is empty.
PROFILE_SECTION_TEMPLATE = Template(
    "\n"
    "<USER PROFILE>\n"
    "$profile_block\n"
)

EMPTY_MEMORY_PLACEHOLDER = "(no relevant memory retrieved)"


def shuffle_options(correct: str, incorrect: Sequence[str], rng
                    ) -> Tuple[List[str], str]:
    """(correct answer, distractors) -> (4 shuffled options, gold letter).

    `rng` should be a per-question seeded random.Random. Only the first 3
    distractors are used (PersonaMem-v2 has exactly 3).
    """
    options = list(incorrect)[:3] + [correct]
    rng.shuffle(options)
    return options, LETTERS[options.index(correct)]


def format_options(options: Sequence[str]) -> str:
    return "\n".join(f"{LETTERS[i]}. {o}" for i, o in enumerate(options))


def build_user_prompt(question: str, options: Sequence[str],
                      memory_block: str,
                      profile_block: Optional[str] = None) -> str:
    profile_section = ""
    if profile_block and profile_block.strip():
        profile_section = PROFILE_SECTION_TEMPLATE.substitute(
            profile_block=profile_block.strip())
    return USER_PROMPT_TEMPLATE.substitute(
        memory_block=(memory_block.strip() if memory_block and memory_block.strip()
                      else EMPTY_MEMORY_PLACEHOLDER),
        profile_section=profile_section,
        question=question.strip(),
        options_block=format_options(options),
    )


def build_messages(question: str, options: Sequence[str], memory_block: str,
                   profile_block: Optional[str] = None) -> List[dict]:
    """Return [{"role": "system", ...}, {"role": "user", ...}] for chat completion."""
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": build_user_prompt(
            question, options, memory_block, profile_block)},
    ]


def parse_answer(raw: str, options: Optional[Sequence[str]] = None) -> str:
    """Model output -> 'A'..'D'; '' if no option can be identified.

    Three fallbacks: (1) the first standalone letter A-D; (2) output identical to
    one option's text; (3) output containing exactly one option's text.
    (2) and (3) require `options`.
    """
    if not raw:
        return ""
    text = str(raw).strip()

    # (1) first A-D letter that is not part of a word ("Amy" does not count)
    for i, ch in enumerate(text.upper()):
        if ch in LETTERS:
            prev_ok = i == 0 or not text[i - 1].isalnum()
            nxt_ok = i + 1 >= len(text) or not text[i + 1].isalnum()
            if prev_ok and nxt_ok:
                return ch

    if not options:
        return ""

    norm = text.lower()
    # (2) exact match with an option's text
    for i, o in enumerate(options):
        if norm == str(o).strip().lower():
            return LETTERS[i]
    # (3) unique containment
    hits = [LETTERS[i] for i, o in enumerate(options)
            if str(o).strip().lower() and str(o).strip().lower() in norm]
    return hits[0] if len(hits) == 1 else ""


# Sampling parameters, identical across baselines.
ANSWER_TEMPERATURE = 0.0
ANSWER_MAX_TOKENS = 32      # one letter; the margin keeps short prefixes parsable


if __name__ == "__main__":                       # print an example prompt
    import random
    opts, gold = shuffle_options(
        "Book the quiet corner table you liked at Rosetta.",
        ["Book the chef's counter so you can chat with the staff.",
         "Try the new rooftop bar — it's loud but trendy.",
         "Order delivery instead of going out."],
        random.Random(0))
    msgs = build_messages(
        question="I want to take my sister out for her birthday this Friday. Ideas?",
        options=opts,
        memory_block=("[2025-03-02] user: I really can't stand noisy restaurants "
                      "these days.\n"
                      "[2025-04-11] user: Rosetta was perfect — we got the corner "
                      "table by the window."),
        profile_block="Prefers quiet, low-stimulation settings; dislikes crowds.")
    for m in msgs:
        print(f"----- {m['role']} -----\n{m['content']}\n")
    print(f"gold = {gold}")
