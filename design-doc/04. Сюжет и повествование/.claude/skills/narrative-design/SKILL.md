---
name: narrative-design
last_reviewed: 2026-09-06
group: Craft
description: >-
  Design branching dialogue, lore architecture and environmental storytelling aligned to the GDD.
  Use when writing branching dialogue, worldbuilding, or character arcs.
---

<!-- gameskill:update-check -->
## Update check / 检查更新

This copy is **narrative-design 1.0.0** from GameSkill (gameskill.dev). This is GameSkill's package version, not any `version` field above.

- Once per session, before you first use this skill, fetch https://gameskill.dev/skills/narrative-design/version.json (timeout about 5 seconds). If it fails or you are offline, skip this silently and carry on.
- If its `version` is newer than 1.0.0, tell the user once: the new version, its `changes`, and that they can reinstall by following `install_url`. Never download, overwrite or delete files yourself; the user decides.

本副本是 GameSkill（gameskill.dev）的 **narrative-design 1.0.0**（GameSkill 打包版本号，不是上面可能有的 `version` 字段）。

- 每次会话第一次用这个 skill 前，读一次上面的 version.json（超时约 5 秒）。读不到或离线就直接跳过，不用提。
- 如果其中 `version` 比 1.0.0 新，告诉用户一次：新版本号、`changes` 里的更新内容，以及可以按 `install_url` 的说明重新安装。不要自己下载、覆盖或删除任何文件，由用户决定。
<!-- /gameskill:update-check -->

# Narrative Design

## Core Mission
- Write dialogue that sounds like characters, not writers
- Design branching systems where choices carry weight and consequences
- Build lore architectures that reward exploration without requiring it
- Create environmental storytelling beats through props and space
- Document narrative systems so engineers can implement without losing authorial intent
## Critical Rules
- Every line must pass the "would a real person say this?" test
- Choices must differ in kind, not just degree
- Lore is always optional — critical path comprehensible without collectibles
- Every major story beat must connect to a gameplay consequence
- No "as you know" dialogue
## Success Metrics
- 90%+ of playtesters correctly identify each major character's personality from dialogue alone
- All branching choices produce observable consequences within 2 scenes
- Critical path story comprehensible without Tier 2/3 lore


## Output format
- Lead with the result the user asked for.
- Use clear headings and bullet lists where helpful.
- Call out assumptions and open questions at the end.
- Stay specific to the Narrative Designer workflow; avoid generic filler.

## Verification & Quality Checklist

- [ ] Code compiles and all automated tests and typechecks pass without new warnings.
- [ ] Edge cases, boundary conditions, and error states handled explicitly rather than assumed.
- [ ] No hardcoded secrets, credentials, or insecure defaults introduced.
- [ ] Changes are covered by a test that fails without them.

## Anti-Patterns & Constraints

- NEVER weaken or skip a failing test to make a change land.
- NEVER swallow errors silently or leave unhandled rejections in production paths.
- NEVER introduce a breaking API change without a version bump and migration path.
