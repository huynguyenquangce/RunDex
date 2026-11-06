# 04 — Figma mobile design

- Date: 2026-11-06
- Tool/model: Claude Code (Sonnet 5.5) + Figma MCP (use_figma)
- Goal: design the iOS and Android screens for RunDex in Figma.

## Prompt (condensed)
```
I want the screen designs on Figma, both Android and iOS, via the Figma MCP.
Design in a modern style, not "AI slop". [AI tried an editorial redesign]
-> "The old design is nice, colors are fine. Restore it. Drop the editorial version."
```

## Result summary
AI created a Figma file with color variables, an Event Card component and 3 screens per platform. It explored an editorial direction, which the owner rejected, so the original design was restored and the alternative deleted.

## Manual fixes / lessons
- SF Pro text does not render in the design tool: iOS frames use Inter.
- Changing fonts after layout collapsed wrapping text; create text with the final font instead.
- The owner preferred the original design over the "less generic" redesign; the decision is theirs.
