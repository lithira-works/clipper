# Architecture Decision Records

Each ADR records one significant decision: its context, the options considered, the decision and its consequences.
ADRs are immutable once accepted. To change a decision, write a new ADR that supersedes the old one.

| # | Title | Status |
|---|---|---|
| [0001](0001-ffmpeg-libass-renderer.md) | ffmpeg + libass as the renderer | Accepted |
| [0002](0002-edit-decision-list.md) | AI outputs an Edit Decision List; rendering is deterministic | Accepted |
| [0003](0003-two-pass-moment-mining.md) | Two-pass moment mining: signals, then Claude | Accepted |
| [0004](0004-redis-arq-queue.md) | Redis + arq for queue and live job state | Accepted |
| 0005 | Auth provider (Clerk vs Better Auth) | Open (CLP-102) |

Template: copy `0000-template.md`, take the next number, and open a PR.
