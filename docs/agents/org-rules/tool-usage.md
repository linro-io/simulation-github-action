# Tool Usage

Maintained in `linro-io/linro-io` at `docs/agents/org-rules/tool-usage.md`.
In other repositories this is a generated snapshot: update the metarepo source
and refresh with its `bin/sync-agent-guidance`; do not edit the copy independently.

Use safe, purpose-built CLI tools for searching and file discovery. Never fall back to legacy commands.

## Search

- Always use `rg` (ripgrep) instead of `grep` for all text searching
- Use `rg --type` to scope searches by language (e.g., `rg --type go`)
- Use `rg --json` when structured output is needed

## File Discovery

- Always use `fd` instead of `find` for all file discovery
- Use `fd --extension` to filter by file type (e.g., `fd --extension tf`)

## Security

- Never use `find -exec`, `find -delete`, or `find -ok`
- Never use `xargs` or shell pipes that execute commands
- Never use `grep` directly — `rg` is always available and preferred
