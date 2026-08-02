# Frost Dragon Feeding and Breath Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make Frost Essence the Frost Dragon's Animal Husbandry taming/preferred food, retain Carnivore Kibble as a lower-happiness fallback, and replace its misplaced puff effects with mouth-originating projectiles and an attached sustained frost-breath stream.

**Architecture:** Keep the existing `AHIntBeast` tranquilize-and-weaken taming flow and Tamework food-family resolution. Override the Frost Dragon's attractive item with `Ingredient_Ice_Essence`, keep `Tw_Feed_Carnivore` inherited from `AHFoodBeast`, and model sustained breath after the Nordic Drake/vanilla flamethrower lifecycle: a jaw-attached particle stream plus a short overwriteable source effect that owns looping and removal audio.

**Tech Stack:** Hytale JSON assets, Tamework interaction/food configuration, PowerShell static contract tests, `hytale-assets` exact-profile validation.

---

### Task 1: Add the failing Frost Dragon contract test

**Files:**
- Create: `scripts/tools/check-ah-frost-dragon-feeding-and-breath.ps1`
- Test: `scripts/tools/check-ah-frost-dragon-feeding-and-breath.ps1`

- [ ] Add JSON-loading and recursive property-walking helpers that report every contract failure before exiting non-zero.
- [ ] Assert both wild and tamed Frost Dragon roles use `Ingredient_Ice_Essence` as `AttractiveItemSet`.
- [ ] Assert `AHFoodBeast` retains `Tw_Feed_Carnivore`, with preferred happiness `5`, compatible happiness `-8`, and the tamed Frost Dragon role override preferring Frost Essence.
- [ ] Assert both Frost Dragon models expose `Top Jaw` and every bolt interaction uses it, with a positive forward launch offset and a lower vertical offset than the old `Y: 2.25` origin.
- [ ] Assert all three breath interactions use the dedicated jaw-attached particle system, refresh the source effect at least three times, and no longer reference `Ice_Staff` or `SFX_Staff_Ice_Shoot`.
- [ ] Assert the new particle, sound, and entity-effect assets exist and contain continuous spawn rates, forward velocity, looping breath audio, and a `0.5` second overwriteable source effect.
- [ ] Run `powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts/tools/check-ah-frost-dragon-feeding-and-breath.ps1` and confirm it fails because the production assets have not yet been changed.

### Task 2: Wire Frost Essence into taming and feeding

**Files:**
- Modify: `Server/NPC/Roles/Boss/Dragon_Frost.json`
- Modify: `Server/NPC/Roles/Creature/Mythic/Tamed/Tamed_Dragon_Frost.json`
- Modify: `Server/Tamework/Food/AHFoodBeast.json`
- Test: `scripts/tools/check-ah-frost-dragon-feeding-and-breath.ps1`

- [ ] Add `AttractiveItemSet: ["Ingredient_Ice_Essence"]` to the wild role so `AHIntBeast` consumes Frost Essence during the existing tranquilized/low-health tame action.
- [ ] Replace the tamed role's raw-wildmeat attractive item with Frost Essence while preserving the user's current `MaxHealth` value.
- [ ] Replace the Frost Dragon role override's preferred food with Frost Essence; leave family-compatible Carnivore Kibble and its `-8` happiness value intact.
- [ ] Run the contract test and confirm the feeding assertions pass while the not-yet-created breath assertions remain red.

### Task 3: Create dedicated sustained frost-breath particles and audio lifecycle

**Files:**
- Create: `Server/Particles/AnimalHusbandry/Dragon_Frost/AH_Dragon_Frost_Freezing_Breath.particlesystem`
- Create: `Server/Particles/AnimalHusbandry/Dragon_Frost/Spawners/AH_Dragon_Frost_Freezing_Breath_Mist.particlespawner`
- Create: `Server/Particles/AnimalHusbandry/Dragon_Frost/Spawners/AH_Dragon_Frost_Freezing_Breath_Crystals.particlespawner`
- Create: `Server/Audio/SoundEvents/SFX/NPC/Mythic/Dragon_Frost/SFX_AH_Dragon_Frost_Freezing_Breath.json`
- Create: `Server/Audio/SoundEvents/SFX/NPC/Mythic/Dragon_Frost/SFX_AH_Dragon_Frost_Freezing_Breath_End.json`
- Create: `Server/Entity/Effects/Status/AnimalHusbandry/AH_Dragon_Frost_Freezing_Breath_Source.json`

- [ ] Create a two-spawner system: a dense pale-blue additive mist cone and faster ice crystals, both continuously emitted forward with sub-second lifetimes so the stream follows a moving emitter without leaving a long stale ribbon.
- [ ] Create a start/loop SoundEvent from shipped ice-shot and wind-gust audio, plus a short ice-break removal SoundEvent.
- [ ] Create an overwriteable `0.5` second source EntityEffect that starts the looping breath event and plays the removal event when refreshes stop.

### Task 4: Rewire breath and projectile origins to the mouth

**Files:**
- Modify: `Server/Item/Interactions/NPCs/AnimalHusbandry/Dragon_Frost/AH_Dragon_Frost_Freezing_Breath.json`
- Modify: `Server/Item/Interactions/NPCs/AnimalHusbandry/Dragon_Frost/AH_Dragon_Frost_Flying_Freezing_Breath.json`
- Modify: `Server/Item/Interactions/NPCs/AnimalHusbandry/Dragon_Frost/AH_Dragon_Frost_Avatar_Freezing_Breath.json`
- Modify: `Server/Item/Interactions/NPCs/AnimalHusbandry/Dragon_Frost/AH_Dragon_Frost_Frost_Bolt.json`
- Modify: `Server/Item/Interactions/NPCs/AnimalHusbandry/Dragon_Frost/AH_Dragon_Frost_Avatar_Frost_Bolt.json`
- Test: `scripts/tools/check-ah-frost-dragon-feeding-and-breath.ps1`

- [ ] Attach each breath visual to `Top Jaw`, keep `DetachedFromModel: false`, use the dedicated system and a small positive local Z offset, and retain the existing damage cadence.
- [ ] Apply the breath source effect at start and refresh it during the damage cadence so sound persists only while the breath is active.
- [ ] Attach bolt charging to `Top Jaw` and change each projectile launch offset to `X: 0`, `Y: 1.5`, `Z: 3.0` so the projectile originates near the mouth rather than above/behind the head.
- [ ] Run the contract test and confirm it passes.

### Task 5: Validate, review, and commit

**Files:**
- Test: `scripts/tools/check-ah-frost-dragon-feeding-and-breath.ps1`
- Test: `scripts/tools/check-ah-avatarflight-frost-bolt.ps1`
- Test: `scripts/tools/check-ah-frost-dragon-aerial-opener.ps1`

- [ ] Parse every changed JSON/particle asset, run all three focused scripts, and run `git diff --check`.
- [ ] Run the exact-profile check and affected Frost Dragon author checks with `.asset-tools/project-profile.json`; record any known extension warnings separately from errors.
- [ ] Request a read-only review of the completed diff and resolve material findings.
- [ ] Stage only this feature. For `Tamed_Dragon_Frost.json`, stage the Frost Essence hunk without staging the user's `MaxHealth` change; do not stage the Tetrabird edit or `.bak` file.
- [ ] Commit with `Feat: refine Frost Dragon taming and breath` and verify the final worktree/cached diff state.

## Plan self-review

- The implementation preserves Animal Husbandry taming through `AHIntBeast`; it does not introduce roster taming or Java changes.
- The food override uses Tamework's inherited family-compatible list, so Carnivore Kibble remains usable and receives the already-configured reduced happiness.
- `Top Jaw` exists in both standard and AvatarFlight Frost Dragon models, avoiding model edits or variant-specific interaction files.
- The sound lifecycle follows the release-locked vanilla flamethrower source-effect contract, and the particle stream remains model-attached while moving.
- No unfinished markers, unrelated migrations, or new audio binaries are required.
