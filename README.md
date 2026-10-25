# MemoryTax

<p align="center">
  <a href="#quickstart">🚀 Quick Start</a> •
  <a href="#repository-layout">📁 Layout</a> •
  <a href="#baselines">🧩 Baselines</a> •
  <a href="#benchmarks">📚 Benchmarks</a> •
  <a href="#results">📊 Results</a>
</p>

Code and results for **"Memory Tax"**: the net value of agent memory over naive retrieval from raw history.

> 🚧 Work in progress. Evaluation harnesses are being cleaned up and will be added per baseline.

## TODO

## Repository layout

```
MemoryTax/
├── bench_data/        # created by common/bench (raw/ and processed/), not tracked
├── common/            # shared by all baselines
│   ├── api/           # OpenAI-compatible chat / embedding clients + reranker, with token / call accounting
│   ├── qa_prompts/    # unified QA prompts per benchmark
│   ├── judge/         # LLM-as-Judge prompts and runner
│   └── bench/         # benchmark download / preparation and evaluated subsets
└── reproduction/
    ├── _naive_rag/    # naive RAG baselines (1-round / 2-round)
    ├── _exp_mem/      # experiential-memory harnesses (e.g., G-Memory, SkillPro)
    └── <baseline>/    # one directory per memory system
        ├── README_<baseline>.md
        ├── setup.sh   # clones the official repo at a pinned commit (+ applies patches)
        ├── patches/   # minimal changes to the official repo, if any
        └── harness/   # our evaluation harness
```

## Baselines

| Method | Category | Reproduction |
|---|---|---|
| [A-Mem](https://github.com/agiresearch/a-mem) | Flat store | [`reproduction/amem`](reproduction/amem) |
| [SimpleMem](https://github.com/aiming-lab/SimpleMem) | Flat store | [`reproduction/simplemem`](reproduction/simplemem) |
| [MemOS](https://github.com/MemTensor/MemOS) | Flat store | [`reproduction/memos`](reproduction/memos) |
| [MemoryOS](https://github.com/BAI-LAB/MemoryOS) | Hier/Lifecycle | [`reproduction/memoryos`](reproduction/memoryos) |
| [LightMem](https://github.com/zjunlp/LightMem) | Hier/Lifecycle | [`reproduction/lightmem`](reproduction/lightmem) |
| [OpenViking](https://github.com/volcengine/OpenViking) | Hier/Lifecycle | [`reproduction/openviking`](reproduction/openviking) |
| [HippoRAG2](https://github.com/OSU-NLP-Group/HippoRAG) | Graph-based | [`reproduction/hipporag2`](reproduction/hipporag2) |
| [PlugMem](https://github.com/TIMAN-group/PlugMem) | Graph-based | [`reproduction/plugmem`](reproduction/plugmem) |
| [MAGMA](https://github.com/FredJiang0324/MAGMA) | Graph-based | [`reproduction/magma`](reproduction/magma) |
| [Mem-T](https://github.com/yanweiyue/Mem-T) | Trained policy | [`reproduction/memt`](reproduction/memt) |
| [Memory-R2](https://github.com/ahmedehabb/Memory-R2) | Trained policy | [`reproduction/memoryr2`](reproduction/memoryr2) |

## Benchmarks

| Benchmark | Evaluated subset |
|---|---|
| LongMemEval-s | full 500 questions (100-question subset for GPT-5.6-luna) |
| PersonaMem-v2 (128k) | 20% (40 personas, 934 questions) |
| MINT-Eval | 10% (60 corpora, 1,557 questions) |

Subset definitions: [`common/bench`](common/bench).

## Quickstart

```bash
python common/bench/download.py   # official benchmark files -> bench_data/raw/
python common/bench/prepare.py    # evaluated subsets -> bench_data/processed/
cp .env.example .env              # fill in API base URLs, keys and model names
cd reproduction/<baseline>
bash setup.sh                     # clone the official repo at the pinned commit
# TODO: harness commands, see README_<baseline>.md
```

## Results

All results are on Hugging Face; [**MemoryTax-Res**](https://huggingface.co/datasets/hexuan21/MemoryTax-Res) is the root repo that indexes the others.

| Repo | Contents |
|---|---|
| [MemoryTax-Res-Qwen3-6-27B](https://huggingface.co/datasets/hexuan21/MemoryTax-Res-Qwen3-6-27B) | Main results with Qwen3.6-27B: QA outputs, judge verdicts, cost, and memory stores |
| [MemoryTax-Res-Qwen3-5-4B](https://huggingface.co/datasets/hexuan21/MemoryTax-Res-Qwen3-5-4B) | Same, with Qwen3.5-4B |
| [MemoryTax-Res-GPT-5-6-luna](https://huggingface.co/datasets/hexuan21/MemoryTax-Res-GPT-5-6-luna) | Same, with GPT-5.6-luna |
| [MemoryTax-Res-experiential-mem](https://huggingface.co/datasets/hexuan21/MemoryTax-Res-experiential-mem) | Experiential-memory results |
| [MemoryTax-Res-world-model-mem](https://huggingface.co/datasets/hexuan21/MemoryTax-Res-world-model-mem) | World-model-memory results |
| [MemoryTax-Res-Other](https://huggingface.co/datasets/hexuan21/MemoryTax-Res-Other) | Extra-benchmark results, RAG ablations, and more intermediates |

## Citation

```bibtex
TODO
```
