# Native Mount Profiles Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:subagent-driven-development` task-by-task. Steps use checkbox syntax for tracking.

**Goal:** Give every approved Animal Husbandry native mount a distinct rider-only base speed, acceleration, and jump force.

**Architecture:** Each profile is a Hytale `MovementConfig` child of `Mount`. A matching tamed role selects it with `MountMovementConfig`; Tamework then applies saddle, level, trait, and talent multipliers to the native rider settings. No companion base multiplier is changed, so unmounted NPC movement remains intact.

**Tech Stack:** Hytale JSON `MovementConfig` assets; AH NPC role variants; existing Tamework native mount integration.

## Global Constraints

- Target the following 32 native tamed roles only; `Tamed_Dragon_Frost` is excluded because it uses `TameworkAvatarFlight`.
- Every new asset inherits `Mount` and overrides only `BaseSpeed`, `Acceleration`, and `JumpForce`.
- Retain vanilla `AutoJumpDisableJumping: true` by inheritance.
- Modify only the `MountMovementConfig` key in each target role's `Modify` object.
- Do not change `BaseMoveSpeedMultiplier`, `MountMode`, anchors, or unrelated dirty checkout files.

### Task 1: Add per-species native movement profiles and role selectors

**Files:**
- Create: `Server/Entity/MovementConfig/AH_Mount_<Species>.json` for each mapping below.
- Modify: the exact `Tamed_*` role in each mapping below.

**Produces:** A one-to-one role-to-profile mapping for all native mounts.

- [ ] Create each profile with exactly this shape, substituting its approved numbers:

```json
{
  "Parent": "Mount",
  "BaseSpeed": 6.2,
  "Acceleration": 0.08,
  "JumpForce": 11
}
```

- [ ] Add the matching `MountMovementConfig` entry in the role's existing `Modify` object. Apply these exact mappings (`role -> asset : BaseSpeed / Acceleration / JumpForce`):

```text
Tamed_Bison -> AH_Mount_Bison : 7.0 / 0.09 / 12
Tamed_Camel -> AH_Mount_Camel : 7.4 / 0.08 / 11
Tamed_Cow -> AH_Mount_Cow : 6.2 / 0.08 / 11
Tamed_Horse -> AH_Mount_Horse : 9.2 / 0.15 / 16
Tamed_Mosshorn -> AH_Mount_Mosshorn : 7.0 / 0.10 / 13
Tamed_Mosshorn_Plain -> AH_Mount_Mosshorn_Plain : 7.6 / 0.12 / 14
Tamed_Ram -> AH_Mount_Ram : 7.2 / 0.13 / 15
Tamed_Antelope -> AH_Mount_Antelope : 9.0 / 0.17 / 16
Tamed_Crab -> AH_Mount_Crab : 5.0 / 0.06 / 9
Tamed_Deer_Stag -> AH_Mount_Deer_Stag : 8.2 / 0.14 / 15
Tamed_Deer_Doe -> AH_Mount_Deer_Doe : 7.5 / 0.13 / 14
Tamed_Horse_Skeleton -> AH_Mount_Horse_Skeleton : 9.3 / 0.16 / 16
Tamed_Horse_Skeleton_Armored -> AH_Mount_Horse_Skeleton_Armored : 8.4 / 0.12 / 14
Tamed_Lobster -> AH_Mount_Lobster : 5.2 / 0.06 / 9
Tamed_Moose_Bull -> AH_Mount_Moose_Bull : 7.1 / 0.09 / 12
Tamed_Moose_Cow -> AH_Mount_Moose_Cow : 6.7 / 0.09 / 12
Tamed_Tetrabird -> AH_Mount_Tetrabird : 8.0 / 0.15 / 15
Tamed_Tortoise -> AH_Mount_Tortoise : 4.2 / 0.05 / 9
Tamed_Trillodon -> AH_Mount_Trillodon : 6.4 / 0.09 / 12
Tamed_Bear_Grizzly -> AH_Mount_Bear_Grizzly : 6.8 / 0.10 / 11
Tamed_Bear_Polar -> AH_Mount_Bear_Polar : 7.0 / 0.10 / 11
Tamed_Crocodile -> AH_Mount_Crocodile : 5.8 / 0.07 / 10
Tamed_Emberwulf -> AH_Mount_Emberwulf : 9.1 / 0.18 / 16
Tamed_Leopard_Snow -> AH_Mount_Leopard_Snow : 9.0 / 0.18 / 16
Tamed_Raptor_Cave -> AH_Mount_Raptor_Cave : 8.7 / 0.16 / 15
Tamed_Rex_Cave -> AH_Mount_Rex_Cave : 7.4 / 0.10 / 12
Tamed_Scorpion -> AH_Mount_Scorpion : 6.4 / 0.13 / 11
Tamed_Spider -> AH_Mount_Spider : 7.4 / 0.16 / 15
Tamed_Spider_Cave -> AH_Mount_Spider_Cave : 7.1 / 0.15 / 15
Tamed_Tiger_Sabertooth -> AH_Mount_Tiger_Sabertooth : 8.7 / 0.16 / 15
Tamed_Wolf_Black -> AH_Mount_Wolf_Black : 8.6 / 0.17 / 15
Tamed_Wolf_White -> AH_Mount_Wolf_White : 8.4 / 0.16 / 15
```

- [ ] Parse every created/modified JSON document and run a static script that verifies: exactly 32 profiles, every profile inherits `Mount`, every profile has only the four permitted keys, every target role references its intended profile exactly once, and no AvatarFlight role was changed.

- [ ] Commit only the profiles and role-selector edits with message `Feat: tune native mount movement profiles`.

### Task 2: Validate the authored batch and update the reference note

**Files:**
- Modify if needed: `wiki/Reference-Library/Mountable-Mobs-Reference.md`.

**Consumes:** The 32 profiles and role selectors from Task 1.

- [ ] Run exact-profile HytaleNpcAssetTools validation if a matching release profile is available. Otherwise record the missing exact profile as a validation limitation and use Workshop release/0.5.7 plus local JSON and reference checks.
- [ ] Verify that the only mountable tamed role without a native `MountMovementConfig` is `Tamed_Dragon_Frost`, whose `MountMode` is `TameworkAvatarFlight`.
- [ ] If the wiki reference lacks it, add one concise note that Frost Dragon is an AvatarFlight mount and deliberately does not use native movement profiles.
- [ ] Commit any documentation-only change separately with message `Docs: clarify Frost Dragon mount movement`.
