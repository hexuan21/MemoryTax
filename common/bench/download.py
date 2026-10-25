"""Download the official benchmark files into bench_data/raw/, pinned to the
revisions used in the paper.

    python common/bench/download.py [--root bench_data]

Only the files needed for the evaluated subsets are fetched: for PersonaMem-v2,
the benchmark CSV and the 40 chat histories listed in
`subset_ids/persona_mem_v2_128k_40.json` (instead of all 200).

Requires `huggingface_hub`. Set `HF_TOKEN` if you hit rate limits.
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import time

from huggingface_hub import hf_hub_download

HERE = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(os.path.dirname(HERE))

SOURCES = {
    "longmemeval": {
        "repo": "xiaowu0162/longmemeval",
        "revision": "2ec2a557f339b6c0369619b1ed5793734cc87533",
        "files": {"longmemeval_s": "longmemeval_s.json"},
    },
    "persona_mem_v2": {
        "repo": "bowen-upenn/PersonaMem-v2",
        "revision": "ed956dea41521fc4499acbc63f966e0fd3c053ba",
        "files": {"benchmark/text/benchmark.csv": "benchmark/text/benchmark.csv"},
    },
    "mint_eval": {
        "repo": "dinobby/MINTEval",
        "revision": "9b9c5befc5126a4ca0fd88cc03c03260142a0883",
        "files": {f"data/{t}-00000-of-00001.parquet": f"{t}.parquet"
                  for t in ("multi_turn_dialogue", "state_tracking",
                            "github_commits", "wiki_revisions")},
    },
}


def persona_history_files():
    sub = json.load(open(os.path.join(HERE, "subset_ids", "persona_mem_v2_128k_40.json")))
    return {p["chat_history_128k_link"]: p["chat_history_128k_link"] for p in sub["personas"]}


def fetch(repo, revision, remote, dst, retries=5):
    if os.path.exists(dst):
        return
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    for a in range(retries):
        try:
            p = hf_hub_download(repo, remote, repo_type="dataset", revision=revision)
            shutil.copyfile(p, dst + ".tmp")
            os.replace(dst + ".tmp", dst)
            return
        except Exception as e:                    # rate limits are common
            if a == retries - 1:
                raise
            wait = 20 * 2 ** a
            print(f"  retry {a + 1}/{retries} {remote}: {type(e).__name__} -> {wait}s")
            time.sleep(wait)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=os.path.join(REPO_ROOT, "bench_data"))
    args = ap.parse_args()
    SOURCES["persona_mem_v2"]["files"].update(persona_history_files())
    for name, src in SOURCES.items():
        print(f"{name}: {src['repo']}@{src['revision'][:10]} ({len(src['files'])} files)")
        for remote, local in src["files"].items():
            fetch(src["repo"], src["revision"], remote,
                  os.path.join(args.root, "raw", name, local))
    print(f"done -> {os.path.join(args.root, 'raw')}")


if __name__ == "__main__":
    main()
