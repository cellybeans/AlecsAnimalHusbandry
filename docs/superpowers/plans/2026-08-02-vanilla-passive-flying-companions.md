# Vanilla Passive Flying Companions Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add favorite-food attraction, taming, land/flight companion commands, and the full Animal Husbandry lifecycle to all 17 vanilla roles that inherit Hytale 0.5.7's `Template_Birds_Passive`.

**Architecture:** Preserve one shared wild aerial template and one shared tamed aerial template, with reusable JSON instruction components for item attraction and controller-mode transitions. Keep every species as a thin wild/tamed variant and use one higher-priority aerial companion config to expose Tamework's flight toggle only for the targeted tamed roles.

**Tech Stack:** Hytale 0.5.7 NPC JSON assets; Alec's Tamework 3.0.0 action/sensor/config surface; HytaleNpcAssetTools exact-profile candidate validation; Python 3 static consistency verifier.

## Global Constraints

- Target exactly: Bluebird, Sparrow, Parrot, Raven, Crow, Finch_Green, Woodpecker, Owl_Brown, Owl_Snow, Bat, Bat_Ice, Pigeon, Duck, Archaeopteryx, Hawk, Pterodactyl, and Vulture.
- Exclude Flamingo, Penguin, Tetrabird, Chicken, Turkey, Temple/test roles, mounts, and all combat behavior.
- Preserve vanilla appearance, drops, flock, health, wander radius, 15-35 block flight envelope, panic, flee, and damage-response behavior.
- Favorite mapping: corn for Bluebird/Sparrow/Finch_Green/Pigeon/Duck/Woodpecker/Crow/Raven; apple for Parrot/Bat/Bat_Ice; raw wild meat for Archaeopteryx/Hawk/Owl_Brown/Owl_Snow/Pterodactyl/Vulture.
- Use hook ID `AnimalHusbandry.Command.ToggleAirborneMode` identically in the Tamework config and NPC hook consumer.
- Newly tamed or respawned flyers start `Idle`, `AirborneMode=false`, with the Walk controller.
- Idle, Follow, and Hold must each support land and flight modes; Hold in flight mode hovers and does not land.
- Follow, Hold, Move to Location, Set Home, Return Home, Recall, needs, happiness, eating, drinking, sleeping, breeding, traits, talents, leveling, and Soul Lantern support remain enabled.
- Defend, Aggressive, Attack Target, and every combat action remain disabled.
- Do not publish this feature before the current Tamework FlightToggle work is committed and released.
- Do not modify or commit the unrelated dirty Frost Dragon, Tetrabird, `.bak`, Avatar Flight, or Tamework files.
- Use Git Bash explicitly via `C:/Program Files/Git/bin/bash.exe`.
- Asset source writes are authorized by the user's `implement` instruction, but each batch still requires a read-only candidate, exact-profile validation, materialization preview, and guarded materialization.
- No Java production changes or Java unit tests are required. The approved asset-test contract is a focused Python consistency verifier plus exact-profile static validation.

## File Structure

- Create `tools/verify_flying_companions.py`: deterministic structural contract for templates, all species pairs, food maps, command flags, and config membership.
- Create `Server/NPC/Roles/_Core/Components/AH_Component_Tamework_Instruction_Aerial_Follow_Item.json`: wild Fly -> safe landing -> grounded approach flow.
- Create `Server/NPC/Roles/_Core/Components/AH_Component_Tamework_Instruction_Aerial_Mode_Transition.json`: tamed hook consumer and Walk/Fly transitions.
- Modify `Server/NPC/Roles/_Core/Templates/AH_Template_Aerial_Neutral.json`: vanilla-priority wild behavior plus favorite-item/taming integration.
- Modify `Server/NPC/Roles/_Core/Templates/AH_Template_Aerial_Tamed.json`: landed default, land/flight Idle/Follow/Hold, grounded husbandry activities, and non-combat commands.
- Keep `Server/NPC/Roles/_Core/Components/AH_Component_Tamework_Instruction_Follow_Flying.json` as the flight-follow implementation.
- Stop referencing `AH_Component_Tamework_Instruction_Hold_Flying.json` from Hold flight mode because that component intentionally lands; flight Hold uses `BodyMotion: Nothing`.
- Create or modify the 34 species role files listed in Tasks 3 and 4.
- Create `Server/Tamework/Companion/AHCompAerial.json`: higher-priority flight-toggle policy for only the 17 tamed flyers.
- Modify the 15 exact husbandry/group/command/spawner assets listed in Task 5.
- Store candidate envelopes and reports only under ignored `.asset-tools/reports/flying-companions/`; never commit them.

---

### Task 1: Wild favorite-item flight, landing, grounded approach, and vanilla return

**Files:**
- Create: `tools/verify_flying_companions.py`
- Create: `Server/NPC/Roles/_Core/Components/AH_Component_Tamework_Instruction_Aerial_Follow_Item.json`
- Modify: `Server/NPC/Roles/_Core/Templates/AH_Template_Aerial_Neutral.json`

**Interfaces:**
- Consumes: Tamework builder IDs `TameworkSetFlyingCompanionMode`; Hytale sensors/actions `ItemInHand`, `ReadPosition`, `StorePosition`, `TakeOff`, `Seek`, `MaintainDistance`, `Land`, `ReleaseTarget`, and `State`.
- Produces: component interface `AnimalHusbandry.Instruction.AerialFollowItem`; states `FollowItem`, `FollowItemLanding`, and `FollowItemGrounded`; target slots `InteractionTarget` and `AH_Aerial_Favorite_Landing`; verifier scope `wild-shared`.

- [ ] **Step 1: Add the failing shared-asset verifier**

Create `tools/verify_flying_companions.py` with these constants and checks. Keep `--scope` required so later unimplemented scopes do not fail earlier task commits.

```python
from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HOOK_ID = "AnimalHusbandry.Command.ToggleAirborneMode"
WILD_COMPONENT = ROOT / "Server/NPC/Roles/_Core/Components/AH_Component_Tamework_Instruction_Aerial_Follow_Item.json"
MODE_COMPONENT = ROOT / "Server/NPC/Roles/_Core/Components/AH_Component_Tamework_Instruction_Aerial_Mode_Transition.json"
WILD_TEMPLATE = ROOT / "Server/NPC/Roles/_Core/Templates/AH_Template_Aerial_Neutral.json"
TAMED_TEMPLATE = ROOT / "Server/NPC/Roles/_Core/Templates/AH_Template_Aerial_Tamed.json"

def load(path: Path) -> dict:
    with path.open(encoding="utf-8-sig") as handle:
        return json.load(handle)

def text(path: Path) -> str:
    return path.read_text(encoding="utf-8-sig")

def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)

def check_wild_shared() -> None:
    require(WILD_COMPONENT.exists(), f"missing {WILD_COMPONENT.relative_to(ROOT)}")
    component = load(WILD_COMPONENT)
    require(component.get("Interface") == "AnimalHusbandry.Instruction.AerialFollowItem", "wrong wild interface")
    component_text = text(WILD_COMPONENT)
    for token in ("ItemInHand", "TakeOff", "TameworkSetFlyingCompanionMode", "LandingUseInfoProviderPosition", "MaintainDistance"):
        require(token in component_text, f"wild component missing {token}")
    template_text = text(WILD_TEMPLATE)
    require("AH_Component_Tamework_Instruction_Aerial_Follow_Item" in template_text, "wild template does not consume attraction component")
    for state in ("FollowItem", "FollowItemLanding", "FollowItemGrounded"):
        require(state in template_text, f"wild template missing state {state}")

SCOPES = {"wild-shared": check_wild_shared}

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--scope", choices=sorted(SCOPES), required=True)
    args = parser.parse_args()
    SCOPES[args.scope]()
```

- [ ] **Step 2: Run the verifier and confirm the expected failure**

Run:

```bash
python tools/verify_flying_companions.py --scope wild-shared
```

Expected: FAIL with `missing Server/NPC/Roles/_Core/Components/AH_Component_Tamework_Instruction_Aerial_Follow_Item.json`.

- [ ] **Step 3: Lock the exact profile and builder contracts**

Run from the Animal Husbandry root:

```bash
hytale-assets profile check --project-profile .asset-tools/project-profile.json --json
hytale-assets author inspect --project-profile .asset-tools/project-profile.json --asset AH_Template_Aerial_Neutral --view both --provenance compact --references both --include-advisories actionable --format json --out .asset-tools/reports/flying-companions/wild-before.json
hytale-assets author options --project-profile .asset-tools/project-profile.json --asset AH_Template_Aerial_Neutral --path '$.Instructions' --format json --out .asset-tools/reports/flying-companions/wild-options.json
```

Expected: profile `release-0.5.7`, no identity conflicts, and current-profile availability for every builder named in this task. Stop if Tamework registration and profile options disagree.

- [ ] **Step 4: Build the wild component and template candidate in staging**

Mirror the two target paths below `.asset-tools/staging/flying-companions/`. Start the component with these exact top-level identity and parameter fields, then add the `Content` instruction tree described immediately below:

```json
{
  "Type": "Component",
  "Class": "Instruction",
  "Interface": "AnimalHusbandry.Instruction.AerialFollowItem",
  "Parameters": {
    "AttractiveItemSet": { "Value": [], "TypeHint": "String" },
    "InteractionTargetSlot": { "Value": "InteractionTarget" },
    "LandingPositionSlot": { "Value": "AH_Aerial_Favorite_Landing" },
    "FlightSeekStopDistance": { "Value": 5.0 },
    "GroundApproachDistanceRange": { "Value": [1.5, 2.0] }
  }
}
```

Set `Content` to `Continue:true`, `Sensor:{"Type":"Any"}`, and these ordered instruction branches:

1. A valid target holding `AttractiveItemSet` while Walk uses `TakeOff` with `JumpSpeed: 4`.
2. A valid target holding the item while Fly and farther than `FlightSeekStopDistance` uses `Seek` with `SlowDownDistance: 8`, `StopDistance: 5`, and `RelativeSpeed: 0.4`.
3. A valid close target reads/stores its position in `AH_Aerial_Favorite_Landing`, then runs `TameworkSetFlyingCompanionMode` with `Mode: Hold`, `LandingState: FollowItemLanding`, `GroundedState: FollowItemGrounded`, `DescendStep: 0.12`, `ReissueDelayMs: 50`, `GroundedStableTicks: 3`, `VerticalMovementEpsilon: 0.15`, and `LandingUseInfoProviderPosition: true`.
4. `FollowItemGrounded` + Walk + valid held item uses `MaintainDistance` with `DesiredDistanceRange: [1.5, 2.0]` and speed `0.3`.
5. Item loss while free-flying releases `InteractionTarget` and returns `Idle`; item loss during landing finishes touchdown, releases the target, uses `TakeOff`, and then returns `Idle`.

In `AH_Template_Aerial_Neutral.json`, retain the vanilla-priority panic/flee branches before attraction, add both Walk and Fly controllers, export the three new states, and replace the old grounded-only `.FollowItem` Seek branch with:

```json
{
  "Reference": "AH_Component_Tamework_Instruction_Aerial_Follow_Item",
  "Modify": {
    "AttractiveItemSet": { "Compute": "AttractiveItemSet" },
    "InteractionTargetSlot": "InteractionTarget",
    "LandingPositionSlot": "AH_Aerial_Favorite_Landing",
    "FlightSeekStopDistance": 5.0,
    "GroundApproachDistanceRange": [1.5, 2.0],
    "_ExportStates": ["Idle", "FollowItem", "FollowItemLanding", "FollowItemGrounded"]
  }
}
```

Guard favorite-food desire particles with `!isEmpty(AttractiveItemSetParticles)` so raw-meat roles can intentionally use an empty particle ID.

- [ ] **Step 5: Create and validate the read-only candidate before source writes**

Create the ignored helper `.asset-tools/reports/flying-companions/build_candidate.py` with this complete content. It converts full staged documents into create targets or SHA-guarded top-level RFC 6902 patches, avoiding remembered hashes and incomplete envelopes:

```python
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from hytale_assets.candidate_validation import CandidateTarget
from hytale_assets.scaffolding import ScaffoldBundle

def load(path: Path) -> dict:
    with path.open(encoding="utf-8-sig") as handle:
        return json.load(handle)

def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

def pointer(key: str) -> str:
    return "/" + key.replace("~", "~0").replace("/", "~1")

def operations(before: dict, after: dict) -> list[dict]:
    result: list[dict] = []
    for key in sorted(before.keys() - after.keys()):
        result.append({"op": "remove", "path": pointer(key)})
    for key in sorted(after.keys() - before.keys()):
        result.append({"op": "add", "path": pointer(key), "value": after[key]})
    for key in sorted(before.keys() & after.keys()):
        if before[key] != after[key]:
            result.append({"op": "replace", "path": pointer(key), "value": after[key]})
    return result

parser = argparse.ArgumentParser()
parser.add_argument("--root", type=Path, required=True)
parser.add_argument("--staging", type=Path, required=True)
parser.add_argument("--candidate-out", type=Path, required=True)
parser.add_argument("--bundle-out", type=Path, required=True)
parser.add_argument("--intent", required=True)
parser.add_argument("paths", nargs="+")
args = parser.parse_args()

targets: list[CandidateTarget] = []
for raw in args.paths:
    relative = Path(raw)
    source = args.root / relative
    staged = args.staging / relative
    document = load(staged)
    if source.exists():
        patch = operations(load(source), document)
        if not patch:
            raise SystemExit(f"no staged change for {relative.as_posix()}")
        targets.append(CandidateTarget(
            "patch",
            relative.stem,
            relative.as_posix(),
            expected_sha256=sha256(source),
            operations=tuple(patch),
        ))
    else:
        targets.append(CandidateTarget(
            "create",
            relative.stem,
            relative.as_posix(),
            expected_absent=True,
            asset_kind="json",
            document=document,
        ))

candidate = {
    "formatVersion": 1,
    "intent": args.intent,
    "targets": [target.to_json() for target in targets],
}
bundle = ScaffoldBundle(
    {},
    args.intent,
    "manual-multi-file",
    1,
    tuple(targets),
    status="unvalidated",
)
args.candidate_out.parent.mkdir(parents=True, exist_ok=True)
args.candidate_out.write_text(
    json.dumps(candidate, indent=2) + "\n",
    encoding="utf-8",
)
args.bundle_out.write_text(json.dumps(bundle.to_json(), indent=2) + "\n", encoding="utf-8")
```

Generate the Task 1 candidate and writable bundle with HytaleNpcAssetTools' bundled Python runtime:

```bash
"/c/Users/22ale/AppData/Roaming/Hytale/Modding/HytaleNpcAssetTools/.venv/Scripts/python.exe" .asset-tools/reports/flying-companions/build_candidate.py --root . --staging .asset-tools/staging/flying-companions --candidate-out .asset-tools/reports/flying-companions/wild-candidate.json --bundle-out .asset-tools/reports/flying-companions/wild-bundle.json --intent "Add passive-flyer favorite-item landing behavior" Server/NPC/Roles/_Core/Components/AH_Component_Tamework_Instruction_Aerial_Follow_Item.json Server/NPC/Roles/_Core/Templates/AH_Template_Aerial_Neutral.json
```

Create `.asset-tools/reports/flying-companions/validate_and_materialize.sh`:

```bash
#!/usr/bin/env bash
set -euo pipefail

candidate="$1"
bundle="$2"
prefix="$3"
profile=".asset-tools/project-profile.json"
reports=".asset-tools/reports/flying-companions"

hytale-assets author candidate validate-schema --candidate "$candidate" --pretty
hytale-assets author validate --project-profile "$profile" --patch "$candidate" --scope affected --simulate --out "$reports/${prefix}-validation.json"
hytale-assets author check --project-profile "$profile" --candidate "$candidate" --scope affected --out "$reports/${prefix}-check.json"
hytale-assets author materialize --project-profile "$profile" --enable-writes --bundle "$bundle" --require-validation safe-static --out "$reports/${prefix}-preview.json"
hytale-assets author materialize --project-profile "$profile" --enable-writes --bundle "$bundle" --require-validation safe-static --write --out "$reports/${prefix}-write.json"
```

Make it executable with `chmod +x .asset-tools/reports/flying-companions/validate_and_materialize.sh`.

Run:

```bash
.asset-tools/reports/flying-companions/validate_and_materialize.sh .asset-tools/reports/flying-companions/wild-candidate.json .asset-tools/reports/flying-companions/wild-bundle.json wild
```

Expected: no blocker or regression classification. Review warnings explicitly.

- [ ] **Step 6: Preview, materialize, and verify the wild batch**

Run `python tools/verify_flying_companions.py --scope wild-shared` after the validation/materialization helper completes.

Expected: materialization hashes match the preview and verifier passes.

- [ ] **Step 7: Commit the wild shared behavior**

```bash
git add tools/verify_flying_companions.py Server/NPC/Roles/_Core/Components/AH_Component_Tamework_Instruction_Aerial_Follow_Item.json Server/NPC/Roles/_Core/Templates/AH_Template_Aerial_Neutral.json
git commit -m "Feat: add passive flyer food attraction"
```

### Task 2: Tamed land/flight modes and grounded husbandry activities

**Files:**
- Modify: `tools/verify_flying_companions.py`
- Create: `Server/NPC/Roles/_Core/Components/AH_Component_Tamework_Instruction_Aerial_Mode_Transition.json`
- Modify: `Server/NPC/Roles/_Core/Templates/AH_Template_Aerial_Tamed.json`

**Interfaces:**
- Consumes: `AnimalHusbandry.Command.ToggleAirborneMode`; `Component_Tamework_Instruction_Follow_Advanced`; `AH_Component_Tamework_Instruction_Follow_Flying`; existing Tamework needs-seek landing fields.
- Produces: component interface `AnimalHusbandry.Instruction.AerialModeTransition`; flag `AirborneMode`; landing ray `AH_Aerial_Mode_LandingRay`; verifier scope `tamed-shared`.

- [ ] **Step 1: Extend the verifier and watch it fail**

Add:

```python
def check_tamed_shared() -> None:
    require(MODE_COMPONENT.exists(), f"missing {MODE_COMPONENT.relative_to(ROOT)}")
    component_text = text(MODE_COMPONENT)
    for token in (HOOK_ID, "AirborneMode", "TakeOff", "Land", "AH_Aerial_Mode_LandingRay"):
        require(token in component_text, f"mode component missing {token}")
    template = load(TAMED_TEMPLATE)
    require(template.get("StartState") == "Idle", "tamed template must start Idle")
    require(template.get("InitialMotionController") == "Walk", "tamed template must start Walk")
    template_text = text(TAMED_TEMPLATE)
    require("AH_Component_Tamework_Instruction_Aerial_Mode_Transition" in template_text, "tamed template missing mode transition")
    for token in ("NeedsSeekFlyingLandingEnabled", "BreedPair", "Sleep", "AirborneMode"):
        require(token in template_text, f"tamed template missing {token}")

SCOPES["tamed-shared"] = check_tamed_shared
```

Run `python tools/verify_flying_companions.py --scope tamed-shared`.

Expected: FAIL because the mode-transition component is absent.

- [ ] **Step 2: Create the mode-transition candidate component**

Use this exact component identity before adding the instruction tree specified below:

```json
{
  "Type": "Component",
  "Class": "Instruction",
  "Interface": "AnimalHusbandry.Instruction.AerialModeTransition"
}
```

Set `Content` to a continuing `Any` instruction. Its first branch consumes `TameworkHook` with `HookId:"AnimalHusbandry.Command.ToggleAirborneMode"` and `Consume:true`; nested flag branches flip `AirborneMode`. Add `AirborneMode=true + Walk + AerialGroundedActivity=false` -> clear Status animation + `TakeOff` (`JumpSpeed: 4`). Add `AirborneMode=false + Fly` -> `AdjustPosition` + `SearchRay` named `AH_Aerial_Mode_LandingRay` (`Range: 64`, `Angle: 90`, `Blocks: StoneAndSoil`) + `Land` (`SlowDownDistance: 5`, `StopDistance: 0.5`, `HeightDifference: [-3, 2]`, `GoalLenience: 3`, `DesiredAltitudeWeight: 0`). Reset rays after Walk touchdown.

Gate automatic TakeOff while `Sleep`, `BreedPair`, `NeedsSeekWater`, or `NeedsSeekFood` owns a grounded activity. These states land, complete, then clear their activity flag so the still-selected `AirborneMode` can retake flight.

- [ ] **Step 3: Refactor the tamed template candidate**

Set:

```json
"StartState": "Idle",
"InitialMotionController": "Walk"
```

Reference `AH_Component_Tamework_Instruction_Aerial_Mode_Transition` as a global `Continue: true` instruction. Replace unconditional Follow/Hold mode actions with explicit branches:

```text
Idle + !AirborneMode + Walk -> grounded WanderInCircle
Idle + AirborneMode + Fly -> aerial WanderInCircle
Follow + !AirborneMode + Walk -> Component_Tamework_Instruction_Follow_Advanced
Follow + AirborneMode + Fly -> AH_Component_Tamework_Instruction_Follow_Flying
Hold + !AirborneMode + Walk -> BodyMotion Nothing
Hold + AirborneMode + Fly -> BodyMotion Nothing
```

On Idle/Follow/airborne Hold entry, run `TameworkSetFlyingCompanionMode` with `Mode: Follow` to neutralize stale landing state. Never run the existing landing-oriented `AH_Component_Tamework_Instruction_Hold_Flying` from airborne Hold.

Keep the existing needs configuration exactly enabled:

```json
"NeedsSeekFlyingLandingEnabled": true,
"NeedsSeekFlyingLandingState": "NeedsSeekWater"
```

and the matching `NeedsSeekFood` value. Add blocking landing wrappers before Sleep and BreedPair movement when Fly is active, keep `AirborneMode` unchanged, allow their grounded instruction only after Walk is active, then clear the activity flag on wake/breed completion so flight mode resumes. Preserve all existing ownership, interaction, growth, needs, happiness, feeding, breeding, traits, command-move, and capture references. Keep all combat feature parameters false in species variants.

- [ ] **Step 4: Validate and materialize the tamed shared candidate**

Generate and validate the tamed batch with:

```bash
"/c/Users/22ale/AppData/Roaming/Hytale/Modding/HytaleNpcAssetTools/.venv/Scripts/python.exe" .asset-tools/reports/flying-companions/build_candidate.py --root . --staging .asset-tools/staging/flying-companions --candidate-out .asset-tools/reports/flying-companions/tamed-candidate.json --bundle-out .asset-tools/reports/flying-companions/tamed-bundle.json --intent "Add tamed aerial mode switching" Server/NPC/Roles/_Core/Components/AH_Component_Tamework_Instruction_Aerial_Mode_Transition.json Server/NPC/Roles/_Core/Templates/AH_Template_Aerial_Tamed.json
.asset-tools/reports/flying-companions/validate_and_materialize.sh .asset-tools/reports/flying-companions/tamed-candidate.json .asset-tools/reports/flying-companions/tamed-bundle.json tamed
```

Expected: no blocker/regression; warnings reviewed; preview and write hashes match.

- [ ] **Step 5: Verify and commit the tamed shared behavior**

```bash
python tools/verify_flying_companions.py --scope tamed-shared
git add tools/verify_flying_companions.py Server/NPC/Roles/_Core/Components/AH_Component_Tamework_Instruction_Aerial_Mode_Transition.json Server/NPC/Roles/_Core/Templates/AH_Template_Aerial_Tamed.json
git commit -m "Feat: add aerial companion mode switching"
```

### Task 3: Aerial-directory wild and tamed role variants

**Files:**
- Modify: `tools/verify_flying_companions.py`
- Modify: `Server/NPC/Roles/Avian/Aerial/Bluebird.json`
- Modify: `Server/NPC/Roles/Avian/Aerial/Tamed/Tamed_Bluebird.json`
- Create: `Server/NPC/Roles/Avian/Aerial/Sparrow.json`
- Create: `Server/NPC/Roles/Avian/Aerial/Parrot.json`
- Create: `Server/NPC/Roles/Avian/Aerial/Raven.json`
- Create: `Server/NPC/Roles/Avian/Aerial/Crow.json`
- Create: `Server/NPC/Roles/Avian/Aerial/Finch_Green.json`
- Create: `Server/NPC/Roles/Avian/Aerial/Woodpecker.json`
- Create: `Server/NPC/Roles/Avian/Aerial/Owl_Brown.json`
- Create: `Server/NPC/Roles/Avian/Aerial/Owl_Snow.json`
- Create: `Server/NPC/Roles/Avian/Aerial/Bat.json`
- Create: `Server/NPC/Roles/Avian/Aerial/Bat_Ice.json`
- Create: `Server/NPC/Roles/Avian/Aerial/Tamed/Tamed_Sparrow.json`
- Create: `Server/NPC/Roles/Avian/Aerial/Tamed/Tamed_Parrot.json`
- Create: `Server/NPC/Roles/Avian/Aerial/Tamed/Tamed_Raven.json`
- Create: `Server/NPC/Roles/Avian/Aerial/Tamed/Tamed_Crow.json`
- Create: `Server/NPC/Roles/Avian/Aerial/Tamed/Tamed_Finch_Green.json`
- Create: `Server/NPC/Roles/Avian/Aerial/Tamed/Tamed_Woodpecker.json`
- Create: `Server/NPC/Roles/Avian/Aerial/Tamed/Tamed_Owl_Brown.json`
- Create: `Server/NPC/Roles/Avian/Aerial/Tamed/Tamed_Owl_Snow.json`
- Create: `Server/NPC/Roles/Avian/Aerial/Tamed/Tamed_Bat.json`
- Create: `Server/NPC/Roles/Avian/Aerial/Tamed/Tamed_Bat_Ice.json`

**Interfaces:**
- Consumes: `AH_Template_Aerial_Neutral`, `AH_Template_Aerial_Tamed`.
- Produces: 11 complete wild/tamed role pairs; verifier scope `aerial-species`.

- [ ] **Step 1: Add the exact species map to the verifier and watch it fail**

Add a `SPECIES` dictionary whose Aerial entries are:

```python
SPECIES = {
    "Bluebird": ("Avian/Aerial", "Drop_Bluebird", 15, 15, "Bluebird", "Plant_Crop_Corn_Item", "Want_Food_Corn", ("Tw_Feed_Herbivore",)),
    "Sparrow": ("Avian/Aerial", "Drop_Sparrow", 15, 15, None, "Plant_Crop_Corn_Item", "Want_Food_Corn", ("Tw_Feed_Herbivore",)),
    "Parrot": ("Avian/Aerial", "Drop_Parrot", 12, 29, None, "Plant_Fruit_Apple", "Want_Food_Apple", ("Tw_Feed_Herbivore",)),
    "Raven": ("Avian/Aerial", "Drop_Raven", 15, 49, None, "Plant_Crop_Corn_Item", "Want_Food_Corn", ("Tw_Feed_Herbivore", "Tw_Feed_Carnivore")),
    "Crow": ("Avian/Aerial", "Drop_Crow", 15, 20, None, "Plant_Crop_Corn_Item", "Want_Food_Corn", ("Tw_Feed_Herbivore", "Tw_Feed_Carnivore")),
    "Finch_Green": ("Avian/Aerial", "Drop_Finch_Green", 15, 15, "Finch_Green", "Plant_Crop_Corn_Item", "Want_Food_Corn", ("Tw_Feed_Herbivore",)),
    "Woodpecker": ("Avian/Aerial", "Drop_Woodpecker", 15, 15, None, "Plant_Crop_Corn_Item", "Want_Food_Corn", ("Tw_Feed_Herbivore", "Tw_Feed_Carnivore")),
    "Owl_Brown": ("Avian/Aerial", "Drop_Owl_Brown", 12, 29, "Owl_Brown", "Food_Wildmeat_Raw", "", ("Tw_Feed_Carnivore",)),
    "Owl_Snow": ("Avian/Aerial", "Drop_Owl_Snow", 12, 29, None, "Food_Wildmeat_Raw", "", ("Tw_Feed_Carnivore",)),
    "Bat": ("Avian/Aerial", "Drop_Bat", 15, 15, None, "Plant_Fruit_Apple", "Want_Food_Apple", ("Tw_Feed_Herbivore",)),
    "Bat_Ice": ("Avian/Aerial", "Drop_Bat_Ice", 15, 25, None, "Plant_Fruit_Apple", "Want_Food_Apple", ("Tw_Feed_Herbivore",)),
}
```

Add `check_species(names)` that asserts each wild file references `AH_Template_Aerial_Neutral`, each tamed file references `AH_Template_Aerial_Tamed`, exact appearance/drop/flock/health/radius/food/particle values, wild `TameRoleChange`, tamed `FoodFavorite`/`FoodGeneric`, `CanFollow/CanHold/CanMoveToLocation/CanReturnHome/CanRecall/CanSetHome/CanBreedPair=true`, and `CanDefend/CanAttackTarget=false`. Register `aerial-species` with these 11 names.

Run `python tools/verify_flying_companions.py --scope aerial-species`.

Expected: FAIL on the first missing Sparrow file or Bluebird's old berry mapping.

- [ ] **Step 2: Build all 11 wild/tamed pairs in one candidate**

Every wild role uses this exact shape with values substituted from `SPECIES`:

```json
{
  "Type": "Variant",
  "Reference": "AH_Template_Aerial_Neutral",
  "Modify": {
    "Appearance": "Sparrow",
    "FlockArray": ["Sparrow"],
    "DropList": "Drop_Sparrow",
    "MaxHealth": 15,
    "WanderRadius": 15,
    "IsMemory": true,
    "MemoriesCategory": "Avian",
    "NameTranslationKey": { "Compute": "NameTranslationKey" },
    "AttractiveItemSet": ["Plant_Crop_Corn_Item"],
    "AttractiveItemSetParticles": "Want_Food_Corn",
    "IsTameable": { "Compute": "IsTameable" },
    "TameRoleChange": { "Compute": "TameRoleChange" }
  },
  "Parameters": {
    "NameTranslationKey": { "Value": "server.npcRoles.Sparrow.name", "Description": "Translation key for NPC name display" },
    "IsTameable": { "Value": true, "Description": "Whether this NPC can be tamed." },
    "TameRoleChange": { "Value": "Tamed_Sparrow", "Description": "The role the NPC will change into when it's tamed." }
  }
}
```

Only Bluebird, Finch_Green, Owl_Brown, and Duck add `MemoriesNameOverride` using the table value. Raw-meat roles set `AttractiveItemSetParticles` to `""`.

Every tamed role uses the same species values but references `AH_Template_Aerial_Tamed`, computes its flock entry with Python `f"Tamed_{name}"`, sets `IsMemory:false`, `FoodFavorite:[favorite]`, exact `FoodGeneric`, `AttitudeGroup:"AH_Livestock_Tamed"`, enables the seven non-combat command/breeding flags, and disables Defend/Attack Target.

- [ ] **Step 3: Validate, materialize, verify, and commit the Aerial family**

Build one versioned candidate with SHA-guarded patch targets for both Bluebird files and create targets for the other 20 files. Run schema validation, affected simulation, integrated candidate check, preview, guarded write, then:

```bash
python tools/verify_flying_companions.py --scope aerial-species
git add tools/verify_flying_companions.py Server/NPC/Roles/Avian/Aerial/Bluebird.json Server/NPC/Roles/Avian/Aerial/Sparrow.json Server/NPC/Roles/Avian/Aerial/Parrot.json Server/NPC/Roles/Avian/Aerial/Raven.json Server/NPC/Roles/Avian/Aerial/Crow.json Server/NPC/Roles/Avian/Aerial/Finch_Green.json Server/NPC/Roles/Avian/Aerial/Woodpecker.json Server/NPC/Roles/Avian/Aerial/Owl_Brown.json Server/NPC/Roles/Avian/Aerial/Owl_Snow.json Server/NPC/Roles/Avian/Aerial/Bat.json Server/NPC/Roles/Avian/Aerial/Bat_Ice.json Server/NPC/Roles/Avian/Aerial/Tamed/Tamed_Bluebird.json Server/NPC/Roles/Avian/Aerial/Tamed/Tamed_Sparrow.json Server/NPC/Roles/Avian/Aerial/Tamed/Tamed_Parrot.json Server/NPC/Roles/Avian/Aerial/Tamed/Tamed_Raven.json Server/NPC/Roles/Avian/Aerial/Tamed/Tamed_Crow.json Server/NPC/Roles/Avian/Aerial/Tamed/Tamed_Finch_Green.json Server/NPC/Roles/Avian/Aerial/Tamed/Tamed_Woodpecker.json Server/NPC/Roles/Avian/Aerial/Tamed/Tamed_Owl_Brown.json Server/NPC/Roles/Avian/Aerial/Tamed/Tamed_Owl_Snow.json Server/NPC/Roles/Avian/Aerial/Tamed/Tamed_Bat.json Server/NPC/Roles/Avian/Aerial/Tamed/Tamed_Bat_Ice.json
git commit -m "Feat: add passive aerial companion roles"
```

### Task 4: Fowl and raptor wild/tamed role variants

**Files:**
- Modify: `tools/verify_flying_companions.py`
- Create: `Server/NPC/Roles/Avian/Fowl/Pigeon.json`
- Create: `Server/NPC/Roles/Avian/Fowl/Duck.json`
- Create: `Server/NPC/Roles/Avian/Fowl/Tamed/Tamed_Pigeon.json`
- Create: `Server/NPC/Roles/Avian/Fowl/Tamed/Tamed_Duck.json`
- Create: `Server/NPC/Roles/Avian/Raptor/Archaeopteryx.json`
- Create: `Server/NPC/Roles/Avian/Raptor/Hawk.json`
- Create: `Server/NPC/Roles/Avian/Raptor/Pterodactyl.json`
- Create: `Server/NPC/Roles/Avian/Raptor/Vulture.json`
- Create: `Server/NPC/Roles/Avian/Raptor/Tamed/Tamed_Archaeopteryx.json`
- Create: `Server/NPC/Roles/Avian/Raptor/Tamed/Tamed_Hawk.json`
- Create: `Server/NPC/Roles/Avian/Raptor/Tamed/Tamed_Pterodactyl.json`
- Create: `Server/NPC/Roles/Avian/Raptor/Tamed/Tamed_Vulture.json`

**Interfaces:**
- Consumes: shared templates and `check_species` from Task 3.
- Produces: remaining 6 wild/tamed pairs; verifier scope `fowl-raptor-species`.

- [ ] **Step 1: Extend the species map and watch the family scope fail**

Add:

```python
SPECIES.update({
    "Pigeon": ("Avian/Fowl", "Drop_Pigeon", 15, 20, None, "Plant_Crop_Corn_Item", "Want_Food_Corn", ("Tw_Feed_Herbivore",)),
    "Duck": ("Avian/Fowl", "Drop_Duck", 15, 25, "Duck", "Plant_Crop_Corn_Item", "Want_Food_Corn", ("Tw_Feed_Herbivore", "Tw_Feed_Carnivore")),
    "Archaeopteryx": ("Avian/Raptor", "Drop_Archaeopteryx", 15, 61, None, "Food_Wildmeat_Raw", "", ("Tw_Feed_Carnivore",)),
    "Hawk": ("Avian/Raptor", "Drop_Hawk", 15, 38, None, "Food_Wildmeat_Raw", "", ("Tw_Feed_Carnivore",)),
    "Pterodactyl": ("Avian/Raptor", "Drop_Pterodactyl", 25, 60, None, "Food_Wildmeat_Raw", "", ("Tw_Feed_Carnivore",)),
    "Vulture": ("Avian/Raptor", "Drop_Vulture", 30, 61, None, "Food_Wildmeat_Raw", "", ("Tw_Feed_Carnivore",)),
})
SCOPES["fowl-raptor-species"] = lambda: check_species(("Pigeon", "Duck", "Archaeopteryx", "Hawk", "Pterodactyl", "Vulture"))
```

Run `python tools/verify_flying_companions.py --scope fowl-raptor-species`.

Expected: FAIL on missing Pigeon.

- [ ] **Step 2: Create the 12 role documents with the explicit variant contracts**

Use each fully expanded path in this task's Files list. Do not use brace expansion when creating or staging assets. Each wild file is a `Variant` of `AH_Template_Aerial_Neutral` and sets `Appearance`, wild `FlockArray`, `DropList`, `MaxHealth`, `WanderRadius`, `IsMemory:true`, `MemoriesCategory:"Avian"`, computed `NameTranslationKey`, one-item `AttractiveItemSet`, the exact particle string, computed `IsTameable`, computed `TameRoleChange`, and parameters for the translation key, `IsTameable:true`, and exact `Tamed_` role ID. Duck alone adds `MemoriesNameOverride:"Duck"`.

Each tamed file is a `Variant` of `AH_Template_Aerial_Tamed` and sets the same species fields, `FlockArray` to its exact `Tamed_*` role ID, `IsMemory:false`, one-item `FoodFavorite`, exact `FoodGeneric`, `AttitudeGroup:"AH_Livestock_Tamed"`, `CanFollow`, `CanHold`, `CanMoveToLocation`, `CanReturnHome`, `CanRecall`, `CanSetHome`, and `CanBreedPair` true, plus `CanDefend` and `CanAttackTarget` false. Raw-meat roles use an empty desire-particle value and `FoodGeneric:["Tw_Feed_Carnivore"]`.

- [ ] **Step 3: Validate, materialize, verify, and commit the Fowl/Raptor family**

Use `build_candidate.py` to emit `fowl-raptor-candidate.json` and `fowl-raptor-bundle.json` for the 12 exact paths in this task, then run:

```bash
.asset-tools/reports/flying-companions/validate_and_materialize.sh .asset-tools/reports/flying-companions/fowl-raptor-candidate.json .asset-tools/reports/flying-companions/fowl-raptor-bundle.json fowl-raptor
```

After materialization, run:

```bash
python tools/verify_flying_companions.py --scope fowl-raptor-species
git add tools/verify_flying_companions.py Server/NPC/Roles/Avian/Fowl Server/NPC/Roles/Avian/Raptor/Archaeopteryx.json Server/NPC/Roles/Avian/Raptor/Hawk.json Server/NPC/Roles/Avian/Raptor/Pterodactyl.json Server/NPC/Roles/Avian/Raptor/Vulture.json Server/NPC/Roles/Avian/Raptor/Tamed/Tamed_Archaeopteryx.json Server/NPC/Roles/Avian/Raptor/Tamed/Tamed_Hawk.json Server/NPC/Roles/Avian/Raptor/Tamed/Tamed_Pterodactyl.json Server/NPC/Roles/Avian/Raptor/Tamed/Tamed_Vulture.json
git commit -m "Feat: add passive fowl and raptor companions"
```

Do not stage existing Tetrabird files.

### Task 5: Register the full husbandry lifecycle and flight-toggle policy

**Files:**
- Modify: `tools/verify_flying_companions.py`
- Create: `Server/Tamework/Companion/AHCompAerial.json`
- Modify: `Server/Tamework/Companion/AHCompNeutral.json`
- Modify: `Server/Tamework/CompanionMovement/AHCompanionMovement.json`
- Modify: `Server/Tamework/Food/AHFoodNeutral.json`
- Modify: `Server/Tamework/Happiness/AHHappNeutral.json`
- Modify: `Server/Tamework/Needs/AHNeedsMain.json`
- Modify: `Server/Tamework/Needs/AHNeedsOmnivore.json`
- Modify: `Server/Tamework/Needs/AHNeedsCarnivore.json`
- Modify: `Server/Tamework/Interactions/AHIntNeutral.json`
- Modify: `Server/Tamework/Breeding/AHBreedNeutral.json`
- Modify: `Server/Tamework/Traits/AHTraitNeutral.json`
- Modify: `Server/Tamework/Talents/AHTalentNeutral.json`
- Modify: `Server/Tamework/Leveling/AHLevelNeutral.json`
- Modify: `Server/NPC/Groups/AH_Livestock_Tamed.json`
- Modify: `Server/Tamework/Items/Commands/AHCommLivestock.json`
- Modify: `Server/Tamework/Items/Spawners/AHSpawnSoulLantern.json`

**Interfaces:**
- Consumes: all 17 `Tamed_*` role IDs and `HOOK_ID`.
- Produces: role-scoped flight toggle and full needs/food/happiness/breeding/progression/capture membership; verifier scope `configs`.

- [ ] **Step 1: Add exact config-membership checks and watch them fail**

Add:

```python
TAMED_IDS = tuple(f"Tamed_{name}" for name in SPECIES)
OMNIVORE_IDS = {"Tamed_Crow", "Tamed_Raven", "Tamed_Duck", "Tamed_Woodpecker"}
CARNIVORE_IDS = {"Tamed_Archaeopteryx", "Tamed_Hawk", "Tamed_Owl_Brown", "Tamed_Owl_Snow", "Tamed_Pterodactyl", "Tamed_Vulture"}

def members(relative: str, *keys: str) -> set[str]:
    value = load(ROOT / relative)
    for key in keys:
        value = value[key]
    return set(value)

def role_ids(relative: str) -> set[str]:
    return members(relative, "RoleIds")

def check_configs() -> None:
    aerial = load(ROOT / "Server/Tamework/Companion/AHCompAerial.json")
    require(aerial.get("Parent") == "TwCompanionConfig_Default", "wrong aerial companion parent")
    require(aerial.get("Priority") == 10, "wrong aerial companion priority")
    require(set(aerial.get("RoleIds", [])) == set(TAMED_IDS), "flight toggle role set drift")
    require(aerial["Command"]["FlightToggle"] == {"Enabled": True, "HookId": HOOK_ID}, "flight toggle contract drift")
    for relative in (
        "Server/Tamework/Companion/AHCompNeutral.json",
        "Server/Tamework/CompanionMovement/AHCompanionMovement.json",
        "Server/Tamework/Happiness/AHHappNeutral.json",
        "Server/Tamework/Needs/AHNeedsMain.json",
        "Server/Tamework/Leveling/AHLevelNeutral.json",
        "Server/Tamework/Talents/AHTalentNeutral.json",
    ):
        require(set(TAMED_IDS) <= role_ids(relative), f"missing tamed flyer membership in {relative}")
    wild_and_tamed = set(SPECIES) | set(TAMED_IDS)
    for relative in (
        "Server/Tamework/Interactions/AHIntNeutral.json",
        "Server/Tamework/Breeding/AHBreedNeutral.json",
        "Server/Tamework/Traits/AHTraitNeutral.json",
    ):
        require(wild_and_tamed <= role_ids(relative), f"missing wild/tamed flyer membership in {relative}")
    require(OMNIVORE_IDS <= role_ids("Server/Tamework/Needs/AHNeedsOmnivore.json"), "omnivore needs membership drift")
    require(CARNIVORE_IDS <= role_ids("Server/Tamework/Needs/AHNeedsCarnivore.json"), "carnivore needs membership drift")
    group_ids = members("Server/NPC/Groups/AH_Livestock_Tamed.json", "IncludeRoles")
    require({f"{role_id}*" for role_id in TAMED_IDS} <= group_ids, "livestock group membership drift")
    command_ids = members("Server/Tamework/Items/Commands/AHCommLivestock.json", "AllowedRoles", "Allowlist")
    require(set(TAMED_IDS) <= command_ids, "livestock command membership drift")
    lantern_ids = members("Server/Tamework/Items/Spawners/AHSpawnSoulLantern.json", "AllowedRoles", "Allowlist")
    require(wild_and_tamed <= lantern_ids, "Soul Lantern membership drift")
    food_overrides = load(ROOT / "Server/Tamework/Food/AHFoodNeutral.json")["RoleOverrides"]
    for role_id in wild_and_tamed:
        require(role_id in food_overrides, f"missing food override for {role_id}")

SCOPES["configs"] = check_configs
```

Run `python tools/verify_flying_companions.py --scope configs`.

Expected: FAIL because `AHCompAerial.json` does not exist.

- [ ] **Step 2: Create the dedicated aerial companion config**

```json
{
  "Parent": "TwCompanionConfig_Default",
  "Enabled": true,
  "Priority": 10,
  "RoleIds": [
    "Tamed_Bluebird", "Tamed_Sparrow", "Tamed_Parrot", "Tamed_Raven", "Tamed_Crow", "Tamed_Finch_Green", "Tamed_Woodpecker", "Tamed_Owl_Brown", "Tamed_Owl_Snow", "Tamed_Bat", "Tamed_Bat_Ice", "Tamed_Pigeon", "Tamed_Duck", "Tamed_Archaeopteryx", "Tamed_Hawk", "Tamed_Pterodactyl", "Tamed_Vulture"
  ],
  "Command": {
    "FlightToggle": {
      "Enabled": true,
      "HookId": "AnimalHusbandry.Command.ToggleAirborneMode"
    }
  }
}
```

- [ ] **Step 3: Update every role-scoped registry**

Add all tamed IDs to `AHCompNeutral.RoleIds`, `AHCompanionMovement.RoleIds`, `AHHappNeutral.RoleIds`, `AHNeedsMain.RoleIds`, `AHTalentNeutral.RoleIds`, and `AHLevelNeutral.RoleIds`. Add all wild and tamed IDs to `AHIntNeutral.RoleIds`, `AHBreedNeutral.RoleIds`, and `AHTraitNeutral.RoleIds`. Add the four exact omnivore IDs and six exact carnivore IDs to their higher-priority needs configs.

Add wildcard entries formed by suffixing each exact tamed ID with `*` to `AH_Livestock_Tamed.IncludeRoles`, exact tamed IDs to `AHCommLivestock.AllowedRoles.Allowlist`, and exact wild plus tamed IDs to `AHSpawnSoulLantern.AllowedRoles.Allowlist`.

In `AHFoodNeutral.RoleOverrides`, add one wild and one tamed override for each species. Each override's `Foods.Preferred` is the exact favorite from `SPECIES`; tamed compatible foods match the tuple in `SPECIES`. Keep wild compatible feeds inherited.

Do not remove or reorder existing unrelated role IDs except where deterministic sorted placement is already the file convention.

- [ ] **Step 4: Validate the multi-file config candidate before writes**

Build one envelope with a `create` target for `AHCompAerial` and SHA-guarded patch targets for all 15 modified assets. Confirm the exact-profile config codec exposes `Command.FlightToggle.Enabled` and `Command.FlightToggle.HookId`. Run candidate schema, affected simulation, integrated check, preview, and guarded materialization.

Expected: every tamed flyer resolves the priority-10 aerial config; ground animals still resolve their existing configs; no missing role references.

- [ ] **Step 5: Verify and commit the husbandry registry batch**

```bash
python tools/verify_flying_companions.py --scope configs
git add tools/verify_flying_companions.py Server/Tamework/Companion/AHCompAerial.json Server/Tamework/Companion/AHCompNeutral.json Server/Tamework/CompanionMovement/AHCompanionMovement.json Server/Tamework/Food/AHFoodNeutral.json Server/Tamework/Happiness/AHHappNeutral.json Server/Tamework/Needs/AHNeedsMain.json Server/Tamework/Needs/AHNeedsOmnivore.json Server/Tamework/Needs/AHNeedsCarnivore.json Server/Tamework/Interactions/AHIntNeutral.json Server/Tamework/Breeding/AHBreedNeutral.json Server/Tamework/Traits/AHTraitNeutral.json Server/Tamework/Talents/AHTalentNeutral.json Server/Tamework/Leveling/AHLevelNeutral.json Server/NPC/Groups/AH_Livestock_Tamed.json Server/Tamework/Items/Commands/AHCommLivestock.json Server/Tamework/Items/Spawners/AHSpawnSoulLantern.json
git commit -m "Feat: register aerial companion husbandry"
```

### Task 6: Full consistency, affected-scope validation, and static behavior verification

**Files:**
- No planned source modification; deterministic repairs return to the owning Task 1-5 file list.
- Reports only: `.asset-tools/reports/flying-companions/`.

**Interfaces:**
- Consumes: all previous task outputs.
- Produces: passing structural suite, refreshed exact-profile evidence, final affected-closure check, and an explicit unsupported/live gap list.

- [ ] **Step 1: Add and run the aggregate verifier**

Add:

```python
def check_all() -> None:
    check_wild_shared()
    check_tamed_shared()
    check_species(tuple(SPECIES))
    check_configs()

SCOPES["all"] = check_all
```

Run:

```bash
python tools/verify_flying_companions.py --scope all
```

Expected: PASS with no output.

- [ ] **Step 2: Refresh profile/snapshot evidence and run the final changed-source check**

```bash
hytale-assets profile check --project-profile .asset-tools/project-profile.json --json
hytale-assets author check --project-profile .asset-tools/project-profile.json --changed --base 6f1e156 --scope affected --out .asset-tools/reports/flying-companions/final-check.json
```

Expected: no blocker/regression classification. The affected closure must include all new role consumers and no unintended grounded species.

- [ ] **Step 3: Generate and run supported static verification**

Generate checks for representative roles `Bluebird`, `Bat_Ice`, `Duck`, and `Pterodactyl`, covering:

```text
wild idle without food
held favorite acquisition
flying approach
safe landing and grounded approach
favorite removal before landing
favorite removal during landing
tame role transition
land/flight Idle
land/flight Follow
land/flight Hold
needs water/food landing and return
sleep landing and wake return
breed landing, offspring role, and growth
Recall and Return Home
Soul Lantern capture/restore
```

Run `hytale-assets author verify generate` against the final candidate/changed manifest, followed by `author verify run --mode static`. Store JSON under `.asset-tools/reports/flying-companions/`.

Expected: supported static checks pass. Record runtime animation, real pathfinding, landing stability, multiplayer target contention, and live persistence as explicit gaps; do not claim them as observed because no live run was authorized.

- [ ] **Step 4: Run final JSON and repository safety checks**

```bash
python tools/verify_flying_companions.py --scope all
git diff --check 6f1e156..HEAD
git status --short
```

Confirm the only remaining unstaged files are the user's pre-existing unrelated changes. Confirm no `.asset-tools` reports, `.bak` files, Frost Dragon files, or Tetrabird files are staged.

- [ ] **Step 5: Close any deterministic repair through its owning task**

If Task 6 finds a defect, return to the Task 1-5 batch that owns that exact file, build a new SHA-guarded candidate for that batch's explicit Files list, rerun its verifier scope, and use that task's explicit `git add` command. Commit the repair with message `Fix: complete aerial companion validation`. If all checks pass without source repair, do not create an empty commit.
