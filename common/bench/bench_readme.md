# common/bench

Benchmark data preparation and the exact subsets evaluated in the paper.

## Prepare the data

```bash
python common/bench/download.py   # official files -> bench_data/raw/
python common/bench/prepare.py    # evaluated subsets -> bench_data/processed/
```

Requires `huggingface_hub` and `pyarrow`. Harnesses read only `bench_data/processed/`:

```
bench_data/processed/
├── longmemeval/
│   ├── longmemeval_s.json            # all 500 questions
│   └── longmemeval_s_sub100.json     # 100-question subset
├── persona_mem_v2/
│   ├── benchmark/text/benchmark.csv  # rows of the 40 evaluated personas
│   └── data/chat_history_128k/*.json
└── mint_eval/
    └── {multi_turn_dialogue,state_tracking,github_commits,wiki_revisions}.parquet
```

## Sources

| Benchmark | Hugging Face dataset | Revision | License |
|---|---|---|---|
| LongMemEval | [`xiaowu0162/longmemeval`](https://huggingface.co/datasets/xiaowu0162/longmemeval) (`longmemeval_s`, not the cleaned version) | `2ec2a557f3` | MIT |
| PersonaMem-v2 | [`bowen-upenn/PersonaMem-v2`](https://huggingface.co/datasets/bowen-upenn/PersonaMem-v2) | `ed956dea41` | CC-BY-4.0 |
| MINT-Eval | [`dinobby/MINTEval`](https://huggingface.co/datasets/dinobby/MINTEval) | `9b9c5befc5` | CC-BY-4.0 |

## Subsets

| Benchmark | Evaluated | Full set | Definition |
|---|---|---|---|
| LongMemEval-s | 500 questions (exp for Qwen backbones) / 100 questions (exp for GPT-5.6-luna) | 500 | [`subset_ids/longmemeval_s_sub100.json`](subset_ids/longmemeval_s_sub100.json) |
| PersonaMem-v2 (128k) | 40 personas, 934 questions | 200 personas | [`subset_ids/persona_mem_v2_128k_40.json`](subset_ids/persona_mem_v2_128k_40.json) |
| MINT-Eval | 60 corpora, 1,557 questions | 595 corpora, 15,631 questions | [`subset_ids/mint_eval.json`](subset_ids/mint_eval.json) |

- **LongMemEval-s sub100**: stratified by `question_type`; within each type, questions are sorted by `question_id` and drawn with `random.Random(42).sample`.
- **PersonaMem-v2**: rows of `benchmark.csv` are grouped by `chat_history_128k_link`.
- **MINT-Eval**: whole rows (a corpus plus all its questions) per subdomain (dialogue 10, state tracking 10, GitHub commits 20, wiki revisions 20). Contexts inside a row are never truncated, since "N steps back" questions depend on step indices. Multi-turn dialogue contexts are split from session blocks into turns (`role`, `block_idx`, `turn_idx`); the other subdomains are unchanged.
