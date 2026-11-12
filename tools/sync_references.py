#!/usr/bin/env python3
"""Give every skill its own copy of the reference files it uses.

Claude reliably sees only the folder of the skill it is running (in claude.ai chat,
only that folder is copied into the sandbox), so each skill must carry the
references it mentions, at `references/<file>.md` inside its own folder.

Edit reference files ONLY at their canonical location (CANONICAL below), then run:
    python3 tools/sync_references.py          # copy into every skill that needs them
    python3 tools/sync_references.py --check  # fail if any copy is missing or stale
"""
import re, sys, shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent / "plugins" / "ai-workforce" / "skills"
CANONICAL_HOME = {  # file -> skill folder that owns the original
    **{f: "assign-work" for f in ["approval-policy.md", "approval-queue.md", "brain-upgrades.md",
       "connections.md", "just-in-time.md", "notion-access.md", "owner-corrections.md", "run-modes.md", "run-tracking.md", "talking-to-the-owner.md", "team-roles.md"]},
    # Read-when-needed files: each covers one situation, and is read only when it comes up.
    **{f: "assign-work" for f in ["if-asked-how-safe.md", "if-highlevel.md", "if-no-team-agents.md", "if-notification-missed.md",
       "if-old-task.md", "if-owner-corrects.md", "if-queuing-a-decision.md", "if-run-unfinished.md"]},
    **{f: "inbox-triage" for f in ["if-inbox-gap.md", "if-quick-look.md"]},
    "if-proving-live.md": "workforce-self-test",   # the live acceptance script: only the self-test reads it
    **{f: "setup-workforce" for f in ["interview.md", "notion-schema.md", "page-templates.md"]},
    "scheduled-prompts.md": "schedule-workforce",
    "scheduled-run-rules.md": "schedule-workforce",
    "inbox-coverage.md": "inbox-triage",
}
REF = re.compile(r"references/([a-z0-9-]+\.md)")

def canonical(name):
    return ROOT / CANONICAL_HOME[name] / "references" / name

def needed(skill_dir):
    todo = set(REF.findall((skill_dir / "SKILL.md").read_text()))
    seen = set()
    while todo:
        n = todo.pop()
        if n in seen: continue
        if n not in CANONICAL_HOME:
            sys.exit(f"{skill_dir.name}: references/{n} has no canonical home")
        seen.add(n)
        todo |= set(REF.findall(canonical(n).read_text()))
    return seen

def main(check):
    problems = []
    for skill in sorted(p for p in ROOT.iterdir() if (p / "SKILL.md").exists()):
        need = needed(skill)
        refdir = skill / "references"
        for n in sorted(need):
            src, dst = canonical(n), refdir / n
            if src == dst: continue
            if not dst.exists() or dst.read_bytes() != src.read_bytes():
                problems.append(f"{skill.name}: references/{n} {'stale' if dst.exists() else 'missing'}")
                if not check:
                    refdir.mkdir(exist_ok=True); shutil.copyfile(src, dst)
        if refdir.exists():  # remove copies this skill no longer uses (never originals)
            for f in refdir.glob("*.md"):
                if f.name in CANONICAL_HOME and CANONICAL_HOME[f.name] != skill.name and f.name not in need:
                    problems.append(f"{skill.name}: references/{f.name} unused")
                    if not check: f.unlink()
    if check:
        print("\n".join(problems) or "All skill references present and in sync.")
        sys.exit(1 if problems else 0)
    print(f"Synced ({len(problems)} files updated)." if problems else "Already in sync.")

if __name__ == "__main__":
    main("--check" in sys.argv)
