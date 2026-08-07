# AH 2.0 Promotional Callouts Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Create an AH 2.0 promo image in which the Frost Dragon remains the hero and a small feature ribbon communicates Dragonriding, Flying Companions, and Saddles & Blankets.

**Architecture:** Keep the supplied screenshot immutable. Produce a transparent title overlay and a separate transparent three-card feature ribbon, then alpha-composite both over the screenshot with ImageMagick. Generate the non-text icons as pixel-art elements; use the real AH saddle icon and cyan blanket texture in the equipment card.

**Tech Stack:** OpenAI Image Generation tool, local chroma-key removal helper, ImageMagick 7.

## Global Constraints

- Background source: `C:/Users/22ale/Documents/ShareX/Screenshots/2026-08/HytaleClient_5ktmNt1AHT.jpg`.
- Preserve every pixel of the source screenshot; only add transparent overlays.
- Keep the Frost Dragon unobstructed on the right side.
- Use an icy/snowy mountain pixel-art theme with pale-blue/white faces and navy shadows.
- Title copy: `Alec's Animal Husbandry v2.0` and `Wings of the Frozen North`.
- Feature-card labels: `Dragonriding`, `Flying Companions`, and `Saddles & Blankets`.
- Use `Common/Icons/ItemsGenerated/AH_Saddle.png` and `Common/NPC/Wildlife/Moose/Models/Attachments/Blanket_Cyan.png` as the real equipment-card visual materials.
- Write new deliverables beside the source screenshot without overwriting prior versions.

---

### Task 1: Produce the title and callout overlays

**Files:**
- Read: `C:/Users/22ale/Documents/ShareX/Screenshots/2026-08/HytaleClient_5ktmNt1AHT.jpg`
- Read: `Common/Icons/ItemsGenerated/AH_Saddle.png`
- Read: `Common/NPC/Wildlife/Moose/Models/Attachments/Blanket_Cyan.png`
- Create: `tmp/imagegen/ah-2-0-title.png`
- Create: `tmp/imagegen/ah-2-0-feature-ribbon.png`

**Interfaces:**
- Consumes: the supplied background for layout reference and the two real equipment assets for the equipment card.
- Produces: two RGBA PNGs with transparent corners, suitable for ImageMagick `-composite`.

- [ ] **Step 1: Generate the title lockup on a magenta chroma-key background**

Use the image-generation tool with exactly this visible copy:

```text
Alec's Animal Husbandry v2.0
Wings of the Frozen North
```

Require a restrained icy Hytale-like pixel-art treatment, no pictorial scene,
and an entirely flat `#ff00ff` background.

- [ ] **Step 2: Generate the three-card feature ribbon on a magenta chroma-key background**

Use the image-generation tool to create a horizontal frosted navy ribbon with
three equal cards and these exact labels:

```text
Dragonriding | Flying Companions | Saddles & Blankets
```

Specify an icy wing/mounted-dragon emblem for the first card, a feather/flock
emblem for the second, and a small brown leather saddle over cyan woven-blanket
material for the third. Require the flat `#ff00ff` background and no scene.

- [ ] **Step 3: Remove chroma key and verify alpha**

Run the supplied helper for the title:

```bash
python 'C:/Users/22ale/.codex/skills/.system/imagegen/scripts/remove_chroma_key.py' \
  --input tmp/imagegen/ah-2-0-title-chromakey.png \
  --out tmp/imagegen/ah-2-0-title.png \
  --auto-key border --soft-matte --transparent-threshold 12 \
  --opaque-threshold 220 --despill
magick identify -format '%w x %h %m\\n' tmp/imagegen/ah-2-0-title.png
```

Run the identical command for `ah-2-0-feature-ribbon-chromakey.png`, changing
only the `--input` and `--out` filenames to
`ah-2-0-feature-ribbon-chromakey.png` and `ah-2-0-feature-ribbon.png`.
Expected: both files report `PNG`, and `magick identify -verbose` reports
`TrueColorAlpha` for both files.

### Task 2: Composite and visually validate the final promo image

**Files:**
- Read: `tmp/imagegen/ah-2-0-title.png`
- Read: `tmp/imagegen/ah-2-0-feature-ribbon.png`
- Read: `C:/Users/22ale/Documents/ShareX/Screenshots/2026-08/HytaleClient_5ktmNt1AHT.jpg`
- Create: `C:/Users/22ale/Documents/ShareX/Screenshots/2026-08/HytaleClient_5ktmNt1AHT_promo-v2-feature-ribbon.png`

**Interfaces:**
- Consumes: the two transparent overlays from Task 1.
- Produces: a 2560 x 1392 PNG promotional image.

- [ ] **Step 1: Place the title in the upper-left negative space**

Resize the title to no more than 1050 pixels wide and composite it at an
upper-left position that stays left of the dragon wing.

```bash
magick 'C:/Users/22ale/Documents/ShareX/Screenshots/2026-08/HytaleClient_5ktmNt1AHT.jpg' \
  \( 'tmp/imagegen/ah-2-0-title.png' -resize 1050x \) -geometry +70+115 -composite \
  'C:/Users/22ale/Documents/ShareX/Screenshots/2026-08/HytaleClient_5ktmNt1AHT_promo-v2-feature-ribbon.png'
```

- [ ] **Step 2: Place the feature ribbon below the title**

Resize the ribbon to 1150 pixels wide, place it around `+80+900`, and composite
it over the intermediate output. Keep the full ribbon in the left-side terrain
and away from the Frost Dragon.

```bash
magick 'C:/Users/22ale/Documents/ShareX/Screenshots/2026-08/HytaleClient_5ktmNt1AHT_promo-v2-feature-ribbon.png' \
  \( 'tmp/imagegen/ah-2-0-feature-ribbon.png' -resize 1150x \) -geometry +80+900 -composite \
  'C:/Users/22ale/Documents/ShareX/Screenshots/2026-08/HytaleClient_5ktmNt1AHT_promo-v2-feature-ribbon.png'
```

- [ ] **Step 3: Inspect the rendered result**

Open the final PNG at original size and verify the exact visible copy, that the
Frost Dragon remains the focal point, and that the screenshot has only received
overlay additions. Confirm dimensions with:

```bash
magick identify -format '%w x %h %m\\n' 'C:/Users/22ale/Documents/ShareX/Screenshots/2026-08/HytaleClient_5ktmNt1AHT_promo-v2-feature-ribbon.png'
```

Expected: `2560 x 1392 PNG`.
