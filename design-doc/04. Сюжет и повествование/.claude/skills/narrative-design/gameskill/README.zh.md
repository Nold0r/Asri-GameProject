## 这个 skill 做什么

这个 skill 覆盖分支对话、世界观架构和环境叙事的设计，要求对话像角色本人说的话，选择在种类上不同而不只是程度不同，设定始终可选，每个主要剧情节点都连到一个玩法后果。产出是给工程实现用的叙事设计文档。

## 什么时候用

- 写分支对话和选择后果
- 搭世界观和设定层级
- 写角色弧线和环境叙事节点

## 怎么装

下载本页的 ZIP，把 `narrative-design/` 整个文件夹放进 agent 的 skills 文件夹：Claude Code 用 `.claude/skills/`，Codex、Gemini CLI、OpenCode 用 `.agents/skills/`，Cursor 用 `.cursor/skills/`，Copilot 用 `.github/skills/`，Windsurf 用 `.windsurf/skills/`，然后重启 agent。也可以直接对 agent 说：Install the skill from https://gameskill.dev/skills/narrative-design/install.md

## 最小示例

`gameskill/examples/` 里是一份提灯与飞蛾的叙事文档：`fixtures/good_lantern_moth.json` 是合格样例，`fixtures/bad_same_kind.json`、`bad_flag_unset.json`、`bad_lore_required.json`、`bad_as_you_know.json` 是各类错误样例，`narrative.py` 是校验逻辑，`tests/run_rules.py` 跑检查。

## 我们怎么测的

总分 38/38。在 Python 3.13 下跑 26 项检查：文档必须包含必需章节，缺章节会被检出；每个 beat 和 choice 的字段要完整；选择必须在种类上不同，同种类的会被拒绝；设定可选时通过，关键路径上要求读设定会被拒绝；每个 beat 都要有玩法后果；"as you know" 式对话会被拒绝，真实人物测试通过；每个选择都要有去处，通向空处的会被拒绝；被读取的 flag 必须先被设置，从未设置的会被拒绝；后果要在两幕窗口内出现，超出窗口的会被拒绝；按内容路由到对话、小说写作、战斗设计；输出路径格式正确；合格文档通过校验，四类错误文档各自失败。结果在 `gameskill/test-report.json`。

## 和站内其他 skill 的区别

托管的 `dialogue-systems` 做对话运行时，`visual-novel` 做类型呈现层；这个 skill 只出设计文档：剧情节点、在种类上不同的选择、先设后读的 flag、不放在关键路径上的设定。

## 搭配

- `dialogue-systems`：把对话文档落成运行时
- `visual-novel`：视觉小说类型的呈现层
- `game-design-gdd`：把叙事节点接进 GDD 的玩法系统
