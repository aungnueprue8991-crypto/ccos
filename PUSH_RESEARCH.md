# How to push the full CCOS tree

## Research summary (2026-09-02)

### What works from this agent environment
1. **GitHub MCP `push_files`** — multi-file commits on a branch. Best path available here.
2. **Batch size** — keep payloads under ~50KB / ~5–15 files per commit.
3. **Branch strategy** — push to `full-tree-push`, then open PR to `main`.

### What does NOT work here
- Local `git push` — no `GITHUB_TOKEN` / `gh` auth in the sandbox.
- Git Data API (create blob/tree/commit) — not exposed by connected MCP tools.
- Single 400+ file commit via MCP — payload limits.

### Best method on a developer machine (full tree)
```bash
tar xzf nexus-ccos-production-0.3.0.tar.gz
cd ccos   # or extracted folder
git clone https://github.com/aungnueprue8991-crypto/ccos.git ccos-remote
cd ccos-remote
git checkout -b full-tree-local
# copy full local tree over (preserve .git)
rsync -a --exclude .git --exclude __pycache__ --exclude '*.db' ../ccos/ ./
git add -A
git commit -m "full tree production-0.3.0"
git push -u origin full-tree-local
# open PR to main
```

### Official GitHub API alternative (with PAT)
1. Create blobs for each file
2. Create tree with base_tree
3. Create commit
4. Update ref
See: https://docs.github.com/en/rest/git/trees

### This branch
`full-tree-push` accumulates runtime packages via batched MCP commits.
