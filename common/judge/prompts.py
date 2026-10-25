"""LLM-as-Judge prompts, prompt selection and verdict parsing.

The judge model is fixed across backbones (Qwen3.6-27B, temperature 0, reasoning
disabled), so score differences between backbones are not mixed with differences
in judging ability. Each judge call is a single user message.

| Prompt | Source | Used for |
|---|---|---|
| `GENERAL` | LightMem's LongMemEval judge prompt | all open-ended short-answer questions (default) |
| `PREF` | LightMem's LongMemEval judge prompt | LongMemEval `single-session-preference` questions |
| `PERSONA_MCQ_UNPARSED` | ours | PersonaMem-v2 responses whose option letter could not be parsed |

PersonaMem-v2 is scored by exact letter match; only responses where
`common.qa_prompts.qa_persona_mem_v2.parse_answer` returns '' go to the judge.
The judge sees all four options and the correct option as letter + full text,
because models often quote an option's text instead of giving its letter.

All prompts ask for `{"label": "CORRECT"}` or `{"label": "WRONG"}`.
"""
from __future__ import annotations

import re
from typing import List, Optional, Sequence

JUDGE_PROMPT_VERSION = "judge/unified-v1"

LETTERS = ("A", "B", "C", "D")

# Transcribed verbatim from LightMem (LongMemEval).
GENERAL = """
I will give you a question, a correct answer, and a response from a model. Please check whether the response is correct or not.
If the meaning of response is equivalent to the correct answer or the response contains all the intermediate steps to get the correct answer, you should also answer CORRECT.

Notes:
- For time related questions, both the gold answer and the generated answer can be a specific date, month, year, or a relative time reference (like "last Tuesday" or "next month"). Try your best to convert relative time reference to specific date/time and compare them in the same format - as long as the generated answer refers to the same date or time period as the gold answer, it should be counted as CORRECT.
- For rounding issues, such as the reference answer being 2 months and the generated answer being 2 months and 3 days; These cases should be counted as CORRECT.

Question: {question}
Gold answer: {gold_answer}
Model Response: {generated_answer}

Is the model response correct?

Just return the label CORRECT or WRONG in a json format with the key as "label".
"""

# Transcribed verbatim from LightMem (LongMemEval).
PREF = """
I will give you a question, a rubric for desired personalized response, and a response from a model. Please output CORRECT if the response satisfies the desired response. Otherwise, output WRONG.
The model does not need to reflect all the points in the rubric. The response is correct as long as it recalls and utilizes user's personal information correctly.

Question: {question}
Rubric: {gold_answer}
Model Response: {generated_answer}

You may provide reasoning, but you MUST end your response with your final answer following the format:
Just return the label CORRECT or WRONG in a json format with the key as "label".
"""

# Fallback for PersonaMem-v2 responses without a parsable letter. All options are
# listed so the judge decides which option the response commits to; responses that
# do not commit to exactly one option are WRONG, so ambiguous outputs are not
# rewarded.
PERSONA_MCQ_UNPARSED = """
I will give you a 4-way multiple-choice question, its options, the correct option, and a response from a model whose reply could not be parsed into a clean option letter.

Your job is to decide which option the model's response actually commits to, and whether that is the correct one.

Notes:
- The model often quotes or paraphrases an option's text instead of giving its letter. Match on meaning, not on exact wording.
- Output CORRECT only if the response commits to exactly one option AND that option is the correct one.
- Output WRONG if the response is empty, refuses to answer, hedges between several options, restates the question, or commits to an option that is not the correct one.
- Do not reward a response for merely sounding sensible or helpful. It must select the correct option.

Question: {question}

Options:
{options_block}

Correct option: {gold_letter}. {gold_answer}

Model Response: {generated_answer}

Just return the label CORRECT or WRONG in a json format with the key as "label".
"""

PROMPTS = {"GENERAL": GENERAL, "PREF": PREF,
           "PERSONA_MCQ_UNPARSED": PERSONA_MCQ_UNPARSED}

# PREF may reason before the label; the others return a one-line JSON.
MAX_TOKENS = {"GENERAL": 64, "PREF": 512, "PERSONA_MCQ_UNPARSED": 64}
JUDGE_TEMPERATURE = 0.0

PREFERENCE_TYPES = frozenset({"single-session-preference", "single_session_preference"})


def pick_prompt(bench: str, category: str = "") -> str:
    """Prompt name for a question.

    bench: `longmemeval_s` (and its subsets), `persona_mem_v2_128k`, or `mint_eval`.
    """
    b = str(bench or "")
    if b.startswith("persona_mem_v2"):
        return "PERSONA_MCQ_UNPARSED"
    if b.startswith("longmemeval") and str(category or "").strip().lower() in PREFERENCE_TYPES:
        return "PREF"
    return "GENERAL"


def format_gold(golds: Sequence[str]) -> str:
    """One gold answer as-is; several as a bulleted list."""
    golds = [str(g) for g in golds if str(g).strip()]
    if len(golds) > 1:
        return "\n".join(f"- {g}" for g in golds)
    return golds[0] if golds else ""


def build_messages(bench: str, category: str, question: str, golds: Sequence[str],
                   response: str) -> List[dict]:
    """Judge messages for open-ended questions (GENERAL / PREF)."""
    name = pick_prompt(bench, category)
    if name == "PERSONA_MCQ_UNPARSED":
        raise ValueError("use build_persona_messages() for PersonaMem-v2")
    text = PROMPTS[name].format(question=question, gold_answer=format_gold(golds),
                                generated_answer=response or "(empty)")
    return [{"role": "user", "content": text}]


def build_persona_messages(question: str, options: Sequence[str], gold_letter: str,
                           gold_text: str, response: str) -> List[dict]:
    """Judge messages for an unparsable PersonaMem-v2 response.

    `options` are the full option texts in the shuffled order shown to the model.
    """
    options_block = "\n".join(f"{LETTERS[i]}. {t}" for i, t in enumerate(options))
    text = PERSONA_MCQ_UNPARSED.format(
        question=question, options_block=options_block,
        gold_letter=gold_letter or "?", gold_answer=gold_text,
        generated_answer=response or "(empty)")
    return [{"role": "user", "content": text}]


def parse_verdict(raw: Optional[str]) -> Optional[int]:
    """Judge output -> 1 (CORRECT) / 0 (WRONG) / None (unparsable, counted separately)."""
    text = str(raw or "").strip()
    m = re.search(r'"label"\s*:\s*"?(CORRECT|WRONG)"?', text, re.I)
    if m:
        return 1 if m.group(1).upper() == "CORRECT" else 0
    up = text.upper()
    has_c, has_w = "CORRECT" in up, "WRONG" in up
    if has_c and not has_w:                       # "INCORRECT" contains "CORRECT"
        return 0 if "INCORRECT" in up else 1
    if has_w and not has_c:
        return 0
    if has_c and has_w:                           # both present: the last one wins
        return 1 if up.rfind("CORRECT") > up.rfind("WRONG") and "INCORRECT" not in up else 0
    return None
