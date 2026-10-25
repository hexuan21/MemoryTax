# common/judge

LLM-as-Judge used for all results in the paper: judge model **Qwen3.6-27B**, temperature 0, reasoning disabled, one user message per question, fixed across backbones. `JUDGE_PROMPT_VERSION = "judge/unified-v1"`.

| Benchmark | Scoring |
|---|---|
| LongMemEval-s | `GENERAL`; `PREF` (rubric-based) for `single-session-preference` |
| MINT-Eval | `GENERAL` |
| PersonaMem-v2 | exact match on the parsed option letter; only unparsable responses go to the judge with `PERSONA_MCQ_UNPARSED` |

`prompts.py` holds the prompts, prompt selection (`pick_prompt`), message builders and `parse_verdict`.

TODO: judge runner over a result directory.
