# DESIGN.md — Unagent Studio

> Derived from [docs/design/DESIGN-meta.md](docs/design/DESIGN-meta.md) for the **product** register (impeccable). Light theme forced by PRODUCT.md scene sentence.

## Color strategy

**Restrained** — tinted neutrals + cobalt accent ≤10% (Committed pulse only on the active playback node).

| Token | Hex | OKLCH approx | Role |
|-------|-----|--------------|------|
| `--color-canvas` | `#FFFFFF` | oklch(1 0 0) | Page background (tint slightly toward blue in CSS: `#F7F9FC`) |
| `--color-surface` | `#F1F4F7` | oklch(0.96 0.005 250) | Panels, rails |
| `--color-ink` | `#1C1E21` | oklch(0.25 0.01 250) | Body text |
| `--color-ink-deep` | `#0A1317` | oklch(0.18 0.02 230) | Headings, primary ink button |
| `--color-hairline` | `#CED0D4` | oklch(0.86 0.005 250) | Borders |
| `--color-accent` | `#0064E0` | oklch(0.55 0.18 255) | Primary actions, selection, sim focus |
| `--color-accent-deep` | `#0457CB` | oklch(0.48 0.17 255) | Accent pressed |
| `--color-success` | `#31A24C` | oklch(0.65 0.15 145) | FlipToDet / stable |
| `--color-warning` | `#F7B928` | oklch(0.82 0.15 90) | Strengthen / caution |
| `--color-critical` | `#E41E3F` | oklch(0.58 0.2 20) | Errors / diverge |

Never pure `#000` / `#FFF` for ink/canvas in components — use tinted neutrals above.

## Typography

- **UI sans:** `Optimistic VF`, fallback `Inter`, `system-ui`, `sans-serif` (document license; Inter is OSS fallback).
- Product scale ratio ~1.2: 12 / 14 / 16 / 20 / 24 / 32.
- No display fonts in labels; no gradient text.

## Radius & spacing

- Buttons: pill (`border-radius: 9999px`) for primary/secondary CTAs.
- Cards/panels: 16–24px (`--radius-xl` / `--radius-xxl`).
- Spacing: 4 / 8 / 12 / 16 / 24 / 32 / 48.

## Components (Studio)

- **Graph canvas** — hero; white/soft surface; hairline nodes; cobalt ring on focus/playback.
- **Playback strip** — play/pause/step; 150–250ms state motion only.
- **Inspector** — evidence, Wilson, narrative snippet; no side-stripe accent bars.
- **Proposal rail** — toggles for FlipToDet / STRENGTHEN_SDB / ABSTAIN; export CTA (ink or cobalt pill).
- Empty/error states teach the load path.

## Motion

Ease-out; 150–250ms. No bounce. No orchestrated page-load choreography.

## Absolute bans

Side-stripe cards, gradient text, default glassmorphism, hero-metric templates, identical icon card grids, modal-first flows, purple-on-white AI cliché.
