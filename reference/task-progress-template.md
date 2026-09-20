# Progress Log

> Narrative log for this task. Append-only — never rewrite history. `status`/`updated` live only in the sibling `README.md`'s frontmatter; this file carries no frontmatter of its own (editing it bumps `README.md`'s `updated` field instead).

## Archive Summary

> Only add this section once the first archive chunk exists — a fresh `progress.md` skips straight to `## Log`. Append-only like the log itself: each bullet is written once when its chunk is archived, and never rewritten afterward.

- YYYY-MM-DD–YYYY-MM-DD: 1-3 sentence compressed summary of what that chunk covered and concluded → full entries in [progress-archive-YYYYMMDD-YYYYMMDD.md](progress-archive-YYYYMMDD-YYYYMMDD.md).

## Log

- YYYY-MM-DD: what was done, what was found, what's next.

---

## When and how to split this file

Once this file passes **~20-30 entries or ~150-200 lines**, split it — don't wait until it's ballooned to several hundred lines, and don't just truncate/delete old entries (that violates the archive-over-delete principle).

1. **Pick a cut point.** Keep the most recent ~8-10 entries live in `## Log`. Never split an entry in half.
2. **Move the older entries out, verbatim.** Create a sibling file `progress-archive-{first-archived-entry-date}-{last-archived-entry-date}.md` (dates as `YYYYMMDD`, no internal dashes, taken from the entries it contains — not today's date). Give it this header, then paste the archived entries below it in their original order, unedited:

   ```markdown
   # Progress Log Archive

   > Archived chunk of `progress.md` — entries {YYYY-MM-DD} to {YYYY-MM-DD}, moved out on {today} to keep the live file lean. Content is verbatim and frozen — never edited after archiving. Discovered via the `## Archive Summary` link in `progress.md`, or by listing this task directory directly.

   - YYYY-MM-DD: ...(the archived entries, copied exactly as they were)
   ```

3. **Append one summary bullet, never rewrite existing ones.** In the live `progress.md`'s `## Archive Summary` section, add a bullet for this newly-archived chunk: date range, a compressed 1-3 sentence summary of what happened/was concluded, and the link to the archive file. This is the *only* place detail gets compressed — the archive file itself keeps full, unabridged detail forever. If someone later needs the specifics behind a summary bullet, the link is the way back to the original entries — nothing is lost, only relocated.
4. **Archive files are frontmatter-exempt**, exactly like `progress.md` itself — they're not scanned into `docs/INDEX.md`. Discoverability comes from the `## Archive Summary` links and from directory listing, not from the index automation.
5. **Never delete an archive file.** It serves as the audit/traceability record — deleting it turns every summary bullet pointing at it into a dead link. If a chunk truly must go, remove or annotate its summary bullet first so the live file never links to something gone.

## Maintenance note

Editing this file bumps the sibling `README.md`'s `updated` field, not this file's own frontmatter (it has none). After creating or editing an archive chunk, no `sync_bundle.py` rerun is needed — archive files are outside its scan scope, same as `progress.md`.
