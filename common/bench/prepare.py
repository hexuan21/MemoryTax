"""Build the evaluated benchmark subsets from bench_data/raw/ into
bench_data/processed/, in the format the harnesses read.

    python common/bench/prepare.py [--root bench_data]

Output:

    bench_data/processed/
    ├── longmemeval/
    │   ├── longmemeval_s.json            # all 500 questions (official file)
    │   └── longmemeval_s_sub100.json     # 100-question subset
    ├── persona_mem_v2/
    │   ├── benchmark/text/benchmark.csv  # rows of the 40 evaluated personas
    │   └── data/chat_history_128k/*.json # their 128k chat histories
    └── mint_eval/
        └── {multi_turn_dialogue,state_tracking,github_commits,wiki_revisions}.parquet

Processing:
  * LongMemEval-s: the 100-question subset keeps the official question order.
  * PersonaMem-v2: rows and chat histories of the 40 personas in
    `subset_ids/persona_mem_v2_128k_40.json`; files are otherwise unchanged.
  * MINT-Eval: rows listed in `subset_ids/mint_eval.json`, in that order, with
    contexts untouched. Multi-turn dialogue contexts are additionally split from
    session blocks into turns (see `split_block`).
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import re
import shutil

HERE = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(os.path.dirname(HERE))
SUBSETS = os.path.join(HERE, "subset_ids")

MINT_TASKS = {"dialogue": "multi_turn_dialogue", "state": "state_tracking",
              "github": "github_commits", "wiki": "wiki_revisions"}


def _subset(name):
    return json.load(open(os.path.join(SUBSETS, name), encoding="utf-8"))


def _write_json(obj, path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path + ".tmp", "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False)
    os.replace(path + ".tmp", path)


# ------------------------------------------------------------- LongMemEval --
def prepare_longmemeval(raw, out):
    src = os.path.join(raw, "longmemeval", "longmemeval_s.json")
    dst = os.path.join(out, "longmemeval")
    os.makedirs(dst, exist_ok=True)
    shutil.copyfile(src, os.path.join(dst, "longmemeval_s.json"))
    data = json.load(open(src, encoding="utf-8"))
    keep = {q["question_id"] for q in _subset("longmemeval_s_sub100.json")["questions"]}
    sub = [q for q in data if q["question_id"] in keep]
    assert len(sub) == len(keep), f"sub100: found {len(sub)} of {len(keep)} questions"
    _write_json(sub, os.path.join(dst, "longmemeval_s_sub100.json"))
    print(f"longmemeval: 500 -> longmemeval_s.json, {len(sub)} -> longmemeval_s_sub100.json")


# ----------------------------------------------------------- PersonaMem-v2 --
def prepare_persona(raw, out):
    src = os.path.join(raw, "persona_mem_v2")
    dst = os.path.join(out, "persona_mem_v2")
    personas = _subset("persona_mem_v2_128k_40.json")["personas"]
    links = {p["chat_history_128k_link"] for p in personas}

    with open(os.path.join(src, "benchmark", "text", "benchmark.csv"),
              newline="", encoding="utf-8") as f:
        reader = csv.reader(f)
        header = next(reader)
        col = header.index("chat_history_128k_link")
        rows = [r for r in reader if r[col] in links]
    expect = sum(p["n_questions"] for p in personas)
    assert len(rows) == expect, f"persona: {len(rows)} rows, expected {expect}"
    os.makedirs(os.path.join(dst, "benchmark", "text"), exist_ok=True)
    with open(os.path.join(dst, "benchmark", "text", "benchmark.csv"), "w",
              newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(header)
        w.writerows(rows)

    for link in sorted(links):
        p = os.path.join(dst, link)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        shutil.copyfile(os.path.join(src, link), p)
    print(f"persona_mem_v2: {len(links)} personas, {len(rows)} questions")


# --------------------------------------------------------------- MINT-Eval --
ROLE_LINE = re.compile(r"^(user|assistant):\s?(.*)$")


def split_block(text):
    """One dialogue session block -> [(role, content), ...] in order.

    A new turn starts only at a line beginning with `user:` / `assistant:`; other
    lines (blank lines, in-turn headings such as `Pros:`, continuation lines) stay
    in the current turn. The leading `[scenario] ...` line is kept as its own item
    with role "scenario".
    """
    out, role, buf = [], None, []

    def flush():
        if role is not None:
            out.append((role, "\n".join(buf).rstrip()))

    for line in text.split("\n"):
        m = ROLE_LINE.match(line)
        if m:
            flush()
            role, buf = m.group(1), [m.group(2)]
        elif role is None:
            if line.strip():
                out.append(("scenario", line.strip()))
        else:
            buf.append(line)
    flush()
    return out


def dialogue_to_turns(blocks):
    """Contexts of one dialogue row (session blocks) -> turn-level contexts.

    Each turn: content (without the role prefix), role (user / assistant /
    scenario), timestamp (that of its block), block_idx (index of the block in
    the row) and turn_idx (order within the block; -1 for the scenario line).
    """
    turns = []
    for bi, b in enumerate(blocks):
        ts = b.get("timestamp")
        ti = 0
        for role, content in split_block(b.get("content") or ""):
            if not content:
                continue
            turns.append({"content": content, "role": role, "timestamp": ts,
                          "block_idx": bi, "turn_idx": -1 if role == "scenario" else ti})
            if role != "scenario":
                ti += 1
    return turns


def prepare_mint(raw, out):
    import pyarrow as pa
    import pyarrow.parquet as pq

    sub = _subset("mint_eval.json")["variants"]
    dst = os.path.join(out, "mint_eval")
    os.makedirs(dst, exist_ok=True)
    for task in MINT_TASKS.values():
        table = pq.read_table(os.path.join(raw, "mint_eval", f"{task}.parquet"))
        ids = [str(x) for x in table.column("id").to_pylist()]
        want = sub[task]["ids"]
        missing = [i for i in want if i not in ids]
        assert not missing, f"{task}: ids not found {missing[:3]}"
        table = table.take(pa.array([ids.index(i) for i in want]))
        if task == "multi_turn_dialogue":
            ctx = [dialogue_to_turns(c) for c in table.column("contexts").to_pylist()]
            table = table.set_column(table.schema.get_field_index("contexts"),
                                     "contexts", pa.array(ctx))
        pq.write_table(table, os.path.join(dst, f"{task}.parquet"))
        n_q = sum(len(q) for q in table.column("questions").to_pylist())
        print(f"mint_eval/{task}: {table.num_rows} rows, {n_q} questions")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=os.path.join(REPO_ROOT, "bench_data"))
    args = ap.parse_args()
    raw, out = os.path.join(args.root, "raw"), os.path.join(args.root, "processed")
    prepare_longmemeval(raw, out)
    prepare_persona(raw, out)
    prepare_mint(raw, out)
    print(f"done -> {out}")


if __name__ == "__main__":
    main()
