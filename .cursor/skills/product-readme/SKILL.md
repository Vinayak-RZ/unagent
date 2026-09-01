---
name: product-readme
description: >-
  Authors public product README.md files for software people can install and use:
  centered logo, badges, tagline, demo, mission, named techniques that teach the
  current-era ideas the code actually uses, tiny quickstart, and a docs index.
  Colibri / LangChain / vLLM / llama.cpp shape. Use when showcasing an OSS product,
  library, or engine as a landing page. Do not use for a human readable overview
  (readable-readme) or a package-by-package internals dump (extensive-readme).
  Unspecified "make a README" goes to the readme skill. Do not invent a separate
  "informative README" type — teaching lives here.
---

# Product README Authoring

Write the README as a **product landing page that teaches**, not a reference manual
and not a textbook. A stranger on GitHub should know what this is, why it exists,
the clever idea, **what ideas of this era they just learned**, and how to try it —
in the first two screens — then be sent to `docs/` for catalogs.

Primary structure authority: **Colibri**. Also steal from LangChain (tiny install +
ecosystem), vLLM (named technique + real blog link), llama.cpp (badges + quick start).

## When to apply

- User asks for a **product README**, OSS landing page, or "README like Colibri / LangChain / vLLM"
- The repo is something people **install and run**, not an internal notes dump
- User wants a logo, tagline, demo, and "get started" — not every env var
- User wants the landing to be **informative** (teach concepts). That is this skill,
  not a fourth README type.

**Use `readable-readme` instead** for a long human `README.md` people finish in one
sitting. **Use `extensive-readme`** for `docs/EXTENSIVE.md` (every package and file
map, plus ideology/engineering). **Use `readme`** when the user did not name a type —
that skill asks first.

If this run also requested an extensive companion: write `README.md` here, then load
`extensive-readme`. Put this banner **at the top** of `README.md` (after the logo is
fine, before the pitch):

```markdown
> Full internals (every package, file map, how the repo runs): [Extensive README](docs/EXTENSIVE.md)
```

## Workflow

### Phase 1 — Discover

Do not invent features, numbers, or URLs.

1. What people install and the one command that proves it works
2. Positioning: what it is, what it is not, who it is for
3. The 1–5 **named techniques** (not a feature laundry list)
4. Proof: screenshots, terminal recordings, measured numbers already in the repo
5. Existing logo / cover art
6. Real links: docs, Discord, website, license, papers/blogs the code cites
7. Sibling products / ecosystem

### Phase 2 — Length

| Product shape | README length |
|---------------|----------------|
| Small SDK / library (LangChain-like) | Short: logo, pitch, install, why, ecosystem, links |
| Engine / research product (Colibri-like) | Longer: mission, idea, how it works, results, get started, docs index |
| Default | **Colibri-shaped**, skip empty sections |

### Phase 3 — Write

Follow [templates.md](templates.md). Skip sections with nothing true to say.

### Phase 4 — Validate

Run [checklist.md](checklist.md).

## Logo

Search before drawing: `assets/`, `docs/`, `docs/media/`, `public/`, `static/`,
`brand/`, images already in README.

**If a real logo exists:** reuse it. Do not replace it.

**If none exists:** write a **basic SVG wordmark** to `assets/{product}-logo.svg`.

- Geometric mark (circle, bird-like chevron, simple letterform) + product name
- One or two flat colors; no gradients, no 3D, no drop shadows, no emoji-as-logo
- Readable on GitHub light and dark (dark fill, or a version that works on both)
- `width` ~480–560 in the README; `alt` is the tagline or product name
- Center with the same HTML as Colibri (see templates)

Use GenerateImage for a PNG **only** if the user asks for a raster mark. SVG is the
default (GitHub-native, matches Colibri).

Do not generate favicons, OG images, or a media kit unless asked.

## Teaching (mandatory — this is how a product README informs)

Name the clever bets so a newcomer **learns** them from the README. The landing
should make a technically curious reader appreciate **what was built** *and* leave
with knowledge they can reuse on other agent/LLM systems.

For each named idea:

- Memorable name ("JIT for weights", "PagedAttention", "determinism-class flip")
- Mechanism in plain language + one analogy
- Why this idea showed up **now** (one sentence of era context, only if true)
- How **this repo** uses it, refuses it, or narrows a neighbor’s claim
- Honest limits (when it wins / loses)
- 1 verified link (blog, paper, wiki, official docs)

Never invent URLs. WebSearch/WebFetch, or omit the link. Same citation bar as
`extensive-readme` / [further-reading.md](../extensive-readme/further-reading.md).

Screenshots need captions that teach, not "screenshot of the UI".

### Ideas you will learn

Research engines and non-trivial libraries add a section (or fold it into Core
techniques) that teaches the **current-age ideas this codebase actually touches**:
counterfactuals vs scoring a path, evidence ceilings, replay vs resample,
fail-closed abstention, residual LLM nondeterminism, interchange pins, and so on.

Rules:

- Only ideas the tree uses, cites, or explicitly contrasts against
- Each idea is 1–4 short paragraphs, not a paper summary
- Nearby-wrong products get one sentence of contrast, not a roast
- Catalogs, env inventories, and file maps stay in `docs/` / `extensive-readme`

A small SDK can keep this to 1–3 named techniques. A research product should make
the reader smarter about the *field*, not only about the binary.

## Section order (Colibri default)

1. Centered logo
2. Badges + nav (website, Discord, docs, languages, license) — only real URLs
3. Tagline + 1–2 paragraph pitch
4. Positioning blockquote (is / is not / invariant)
5. Proof: terminal demo and/or screenshot with a teaching caption
6. Why it exists / mission
7. **Ideas you will learn** (era concepts + how this repo uses them) — skip only for tiny SDKs whose Core techniques already teach
8. Core techniques (named, measured, honest)
9. The idea (one conceptual explanation)
10. How it works (short; diagrams; details in `docs/`)
11. What it achieves (real numbers only)
12. Get started (install + one run command)
13. Go deeper (doc index table)
14. Repo layout (brief)
15. Community / contributing
16. Acknowledgements (systems this repo actually uses)
17. License

## Quality bar

- First screen answers: what it is, who it is for, how to try it
- A curious reader can name 3 ideas they did not have before opening the file
- One install snippet a newcomer can paste (LangChain-short)
- Named technique linked to a **real** source (vLLM × PagedAttention blog)
- Catalogs, env inventories, and full API tables belong in `docs/` or `extensive-readme`
- Present tense; no engagement bait; no fake benchmarks
- Terminal demos show actual CLI output from this project (or clearly marked as illustrative if you cannot run it)

## Anti-patterns

- Exhaustive numbered manual in the product README
- Generic "Features" bullets with no idea behind them
- Invented logos over an existing brand
- Gradient/3D/slop logos
- Fake stars, fake "trusted by", fake tok/s
- Invented citation URLs
- Empty sections left as placeholders
- A separate “informative README” skill or fourth router type
- Survey-paper dump of famous work the code does not use
- File maps and package catalogs in `README.md` (that is extensive-readme)

## Output

- `README.md` at repo root (or the package the user named)
- Banner to `docs/EXTENSIVE.md` when an extensive companion was requested
- `assets/{product}-logo.svg` only when no logo existed
- Do not write the extensive dump yourself — load `extensive-readme`

## Additional resources

- Skeleton and HTML snippets: [templates.md](templates.md)
- Annotated OSS patterns: [examples.md](examples.md)
- Pre-ship checklist: [checklist.md](checklist.md)
