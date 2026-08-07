# Explicit Breeding Balance Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Give all 94 breeding-eligible tamed adult roles explicit breeding cooldown and growth-time values.

**Architecture:** Keep the existing three Tamework breeding assets and expand only their `RoleOverrides` maps. Preserve all beast profiles, livestock baby-role families, and deer/moose gendered families; add explicit cooldown objects and lifecycle timing using the approved balance matrix.

**Tech Stack:** Hytale 0.5.7 JSON assets, Tamework `TwBreedingConfig`, HytaleNpcAssetTools, Node.js for read-only resolution checks, Git Bash.

## Global Constraints

- Use the locked `release-0.5.7` project profile at `.asset-tools/project-profile.json`.
- Keep all 29 profiles in `AHBreedBeast.json` unchanged.
- Use `MinDelaySeconds = BaseCooldownMinutes * 3` and `MaxDelaySeconds = BaseCooldownMinutes * 9`.
- Preserve existing pairing, gender, inheritance, and lifecycle family structures.
- Add no wild-role or juvenile-role cooldown overrides.
- Add no source-shape or asset-inventory test; use the project's asset-validation workflow and a one-time effective-resolution check.
- The exact approved values are normative in `docs/superpowers/specs/2026-08-07-explicit-breeding-balance-design.md`.

---

### Task 1: Complete Livestock Profiles

**Files:**
- Modify: `Server/Tamework/Breeding/AHBreedLivestock.json`
- Reference: `docs/superpowers/specs/2026-08-07-explicit-breeding-balance-design.md`

**Interfaces:**
- Consumes: Existing `TwBreedingConfig.RoleOverrides` JSON shape and the 20-row livestock matrix.
- Produces: Twenty tamed-adult overrides that each resolve an explicit cooldown and growth time.

- [ ] **Step 1: Record the baseline target set**

Run a Node.js read-only inventory that derives tamed adult roles from `RoleIds`, excluding `_Calf`, `_Chick`, `_Kid`, `_Foal`, `_Lamb`, and `_Piglet`. Confirm the baseline reports 20 targets and zero explicit cooldowns.

- [ ] **Step 2: Add the explicit cooldown objects**

For every livestock matrix row, add this exact shape with the row's base value:

```json
"Cooldowns": {
  "BaseCooldownMinutes": 90,
  "MinDelaySeconds": 270,
  "MaxDelaySeconds": 810
}
```

Compute the two delay fields from the global formula. Insert `Cooldowns` before `OffspringLifecycle` in existing overrides.

- [ ] **Step 3: Complete the lifecycle values**

Keep existing baby-role `Families` arrays and replace only their `TimeToFullGrownMinutes` with the approved matrix value. For Bunny, Mosshorn, Mosshorn Plain, and Rabbit, add a direct lifecycle override:

```json
"OffspringLifecycle": {
  "TimeToFullGrownMinutes": 50
}
```

Use 50 for Bunny/Rabbit and 180 for both Mosshorn variants.

- [ ] **Step 4: Parse and resolve the livestock asset**

Run a Node.js check that parses the JSON and, for all 20 targets, asserts positive explicit `BaseCooldownMinutes`, `MinDelaySeconds`, `MaxDelaySeconds`, and either direct or first-family `TimeToFullGrownMinutes`. Assert the delay formula and `MinDelaySeconds < MaxDelaySeconds`.

- [ ] **Step 5: Review and commit the livestock batch**

Run `git diff --check` and inspect `git diff -- Server/Tamework/Breeding/AHBreedLivestock.json`. Commit only the livestock asset with:

```bash
git add Server/Tamework/Breeding/AHBreedLivestock.json
git commit -m "Balance: add explicit livestock breeding times"
```

### Task 2: Complete Neutral, Critter, and Aerial Profiles

**Files:**
- Modify: `Server/Tamework/Breeding/AHBreedNeutral.json`
- Reference: `docs/superpowers/specs/2026-08-07-explicit-breeding-balance-design.md`

**Interfaces:**
- Consumes: Existing `TwBreedingConfig.RoleOverrides` JSON shape and the 45-row neutral matrix.
- Produces: Forty-five tamed-adult overrides that each resolve an explicit cooldown and growth time while retaining four wild deer/moose resolver overrides.

- [ ] **Step 1: Record the baseline target set**

Run a Node.js read-only inventory that selects the 45 `Tamed_` adult roles from `RoleIds`. Confirm only the four tamed deer/moose roles currently have lifecycle overrides and none has an explicit cooldown.

- [ ] **Step 2: Add ordinary direct overrides**

For roles without lifecycle families, add an entry in `RoleIds` order using this shape and each approved matrix row:

```json
"Tamed_Bluebird": {
  "Cooldowns": {
    "BaseCooldownMinutes": 40,
    "MinDelaySeconds": 120,
    "MaxDelaySeconds": 360
  },
  "OffspringLifecycle": {
    "TimeToFullGrownMinutes": 45
  }
}
```

- [ ] **Step 3: Extend deer and moose without replacing family data**

Add `Cooldowns` to `Tamed_Deer_Doe`, `Tamed_Deer_Stag`, `Tamed_Moose_Bull`, and `Tamed_Moose_Cow`. Retain their `Pairing` objects and `Families` adult-role/gender arrays. Update family growth to 120 for deer and 180 for moose. Leave the four corresponding wild-role overrides otherwise unchanged because wild roles are not breeding eligible.

- [ ] **Step 4: Parse and resolve the neutral asset**

Run the same production-shape resolution check for all 45 tamed adult targets. Assert the delay formula, positive growth values, and preservation of all eight deer/moose family overrides.

- [ ] **Step 5: Review and commit the neutral batch**

Run `git diff --check` and inspect `git diff -- Server/Tamework/Breeding/AHBreedNeutral.json`. Commit only the neutral asset with:

```bash
git add Server/Tamework/Breeding/AHBreedNeutral.json
git commit -m "Balance: add explicit neutral breeding times"
```

### Task 3: Validate the Complete Breeding Configuration

**Files:**
- Verify: `Server/Tamework/Breeding/AHBreedLivestock.json`
- Verify: `Server/Tamework/Breeding/AHBreedNeutral.json`
- Verify unchanged: `Server/Tamework/Breeding/AHBreedBeast.json`

**Interfaces:**
- Consumes: All three materialized breeding assets.
- Produces: Evidence that all 94 eligible tamed adults resolve valid explicit timing without changing established beast values or family structures.

- [ ] **Step 1: Recheck the exact project profile**

```bash
hytale-assets profile check --project-profile .asset-tools/project-profile.json --json
```

Require `status: ready`, game version `0.5.7`, channel `release`, and no conflicts.

- [ ] **Step 2: Run the full effective-resolution check**

Parse all three configs and derive eligible tamed adult roles. For each of the expected 94 targets, resolve the role override and assert:

```text
BaseCooldownMinutes > 0
MinDelaySeconds == BaseCooldownMinutes * 3
MaxDelaySeconds == BaseCooldownMinutes * 9
TimeToFullGrownMinutes > 0
```

For family-based lifecycle entries, read the first family's growth value. Report counts by config: livestock 20, neutral 45, beast 29.

- [ ] **Step 3: Run repository-safe static validation**

From Git Bash, parse every JSON file under `Server/Tamework/Breeding`, run
`git diff --check`, and confirm the effective-resolution check from Step 2
reports all 94 eligible profiles. The repository's broader release validator is
a PowerShell script, so it is out of scope under the workspace's Git Bash-only
instruction. Do not run package publication or live-server validation.

- [ ] **Step 4: Review final state**

Run `git status --short`, `git diff --check`, and review the commits against the approved spec. Confirm no stale `hytale-assets` process remains and no unrelated file changed.
