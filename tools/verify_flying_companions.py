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
TAMED_VARIANT_ROOT = ROOT / "Server/NPC/Roles/Avian/Aerial/Tamed"


def load(path: Path) -> dict:
    with path.open(encoding="utf-8-sig") as handle:
        return json.load(handle)


def text(path: Path) -> str:
    return path.read_text(encoding="utf-8-sig")


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def has_item_target_loss_sensor(sensor: dict) -> bool:
    if sensor.get("Type") != "Not":
        return False
    target = sensor.get("Sensor", {})
    return target.get("Type") == "Target" and any(
        filter_entry.get("Type") == "ItemInHand"
        for filter_entry in target.get("Filters", [])
    )


def has_target_loss_branch(instructions: list[dict], state: str, controller: str, action_types: list[str]) -> bool:
    for instruction in instructions:
        sensors = instruction.get("Sensor", {}).get("Sensors", [])
        if not any(sensor.get("Type") == "State" and sensor.get("State") == state for sensor in sensors):
            continue
        if not any(
            sensor.get("Type") == "MotionController" and sensor.get("MotionController") == controller
            for sensor in sensors
        ):
            continue
        if not any(has_item_target_loss_sensor(sensor) for sensor in sensors):
            continue
        actions = instruction.get("Actions", [])
        if [action.get("Type") for action in actions] != action_types:
            continue
        if not actions or actions[0].get("TargetSlot", {}).get("Compute") != "InteractionTargetSlot":
            continue
        if actions[-1].get("Type") != "State" or actions[-1].get("State") != "Idle":
            continue
        return True
    return False


def instruction_children(instruction: dict) -> list[dict]:
    children = instruction.get("Instructions", [])
    return children if isinstance(children, list) else []


def descendants(instructions: list[dict]) -> list[dict]:
    result: list[dict] = []
    for instruction in instructions:
        result.append(instruction)
        result.extend(descendants(instruction_children(instruction)))
    return result


def state_branches(template: dict, state: str) -> list[dict]:
    return [
        instruction
        for instruction in descendants(template.get("Instructions", []))
        if instruction.get("Sensor", {}).get("Type") == "State"
        and instruction.get("Sensor", {}).get("State") == state
    ]


def has_flag(sensors: list[dict], name: str, value: bool | None = None) -> bool:
    for sensor in sensors:
        if sensor.get("Type") != "Flag" or sensor.get("Name") != name:
            continue
        if value is None and "Set" not in sensor:
            return True
        if value is False and sensor.get("Set") is False:
            return True
        if value is True and sensor.get("Set") is True:
            return True
    return False


def has_controller(sensors: list[dict], controller: str) -> bool:
    return any(
        sensor.get("Type") == "MotionController" and sensor.get("MotionController") == controller
        for sensor in sensors
    )


def has_conjunction(instructions: list[dict], flags: dict[str, bool | None], controller: str | None = None) -> bool:
    for instruction in descendants(instructions):
        sensor = instruction.get("Sensor", {})
        if sensor.get("Type") != "And":
            continue
        sensors = sensor.get("Sensors", [])
        if any(not has_flag(sensors, name, value) for name, value in flags.items()):
            continue
        if controller is not None and not has_controller(sensors, controller):
            continue
        return True
    return False


def has_body_motion_branch(
    instructions: list[dict],
    flags: dict[str, bool | None],
    controller: str,
    motion_type: str,
    **fields: object,
) -> bool:
    for instruction in descendants(instructions):
        sensor = instruction.get("Sensor", {})
        if sensor.get("Type") != "And":
            continue
        sensors = sensor.get("Sensors", [])
        if any(not has_flag(sensors, name, value) for name, value in flags.items()):
            continue
        if not has_controller(sensors, controller):
            continue
        motions = [instruction.get("BodyMotion", {})]
        motions.extend(
            child.get("BodyMotion", {})
            for child in descendants(instruction_children(instruction))
        )
        if any(
            motion_contains(motion, motion_type, fields)
            for motion in motions
        ):
            return True
    return False


def motion_contains(motion: object, motion_type: str, fields: dict[str, object]) -> bool:
    if isinstance(motion, dict):
        if motion.get("Type") == motion_type and all(motion.get(key) == value for key, value in fields.items()):
            return True
        return any(motion_contains(value, motion_type, fields) for value in motion.values())
    if isinstance(motion, list):
        return any(motion_contains(value, motion_type, fields) for value in motion)
    return False


def has_state_mode_reference(
    template: dict,
    state: str,
    flags: dict[str, bool | None],
    controller: str,
    reference: str,
) -> bool:
    for branch in state_branches(template, state):
        for instruction in descendants(instruction_children(branch)):
            sensor = instruction.get("Sensor", {})
            if sensor.get("Type") != "And":
                continue
            sensors = sensor.get("Sensors", [])
            if any(not has_flag(sensors, name, value) for name, value in flags.items()):
                continue
            if not has_controller(sensors, controller):
                continue
            if has_reference(instruction_children(instruction), reference):
                return True
    return False


def has_state_mode_action(
    template: dict,
    state: str,
    flags: dict[str, bool | None],
    controller: str,
    action_type: str,
    **fields: object,
) -> bool:
    for branch in state_branches(template, state):
        for instruction in descendants(instruction_children(branch)):
            sensor = instruction.get("Sensor", {})
            if sensor.get("Type") != "And":
                continue
            sensors = sensor.get("Sensors", [])
            if any(not has_flag(sensors, name, value) for name, value in flags.items()):
                continue
            if not has_controller(sensors, controller):
                continue
            if has_action([instruction], action_type, **fields):
                return True
    return False


def has_state_action(template: dict, state: str, action_type: str, **fields: object) -> bool:
    for branch in state_branches(template, state):
        if has_action(instruction_children(branch), action_type, **fields):
            return True
    return False


def has_grounded_activity_release(template: dict) -> bool:
    required_states = {"Sleep", "BreedPair", "NeedsSeekWater", "NeedsSeekFood"}
    for instruction in descendants(template.get("Instructions", [])):
        sensor = instruction.get("Sensor", {})
        if sensor.get("Type") != "And":
            continue
        sensors = sensor.get("Sensors", [])
        if not has_flag(sensors, "AerialGroundedActivity"):
            continue
        not_sensor = next((entry.get("Sensor") for entry in sensors if entry.get("Type") == "Not"), None)
        if not_sensor is None or not_sensor.get("Type") != "Or":
            continue
        states = {
            entry.get("State")
            for entry in not_sensor.get("Sensors", [])
            if entry.get("Type") == "State"
        }
        if states != required_states:
            continue
        if any(
            action.get("Type") == "SetFlag"
            and action.get("Name") == "AerialGroundedActivity"
            and action.get("SetTo") is False
            for action in instruction.get("Actions", [])
        ):
            return True
    return False


def has_action(instructions: list[dict], action_type: str, **fields: object) -> bool:
    for instruction in descendants(instructions):
        for action in instruction.get("Actions", []):
            if action.get("Type") != action_type:
                continue
            if all(action.get(key) == value for key, value in fields.items()):
                return True
    return False


def has_reference(instructions: list[dict], reference: str) -> bool:
    return any(instruction.get("Reference") == reference for instruction in descendants(instructions))


def contains_reference(value: object, reference: str) -> bool:
    if isinstance(value, dict):
        if value.get("Reference") == reference:
            return True
        return any(contains_reference(child, reference) for child in value.values())
    if isinstance(value, list):
        return any(contains_reference(child, reference) for child in value)
    return False


def has_initial_flag(template: dict, name: str, value: bool) -> bool:
    for instruction in template.get("Instructions", []):
        sensor = instruction.get("Sensor", {})
        if sensor.get("Type") != "Any" or sensor.get("Once") is not True:
            continue
        if any(
            action.get("Type") == "SetFlag"
            and action.get("Name") == name
            and action.get("SetTo") is value
            for action in instruction.get("Actions", [])
        ):
            return True
    return False


def has_activity_wrapper(template: dict, state: str) -> bool:
    for branch in state_branches(template, state):
        if not any(
            action.get("Type") == "SetFlag"
            and action.get("Name") == "AerialGroundedActivity"
            and action.get("SetTo") is True
            for instruction in descendants(instruction_children(branch))
            for action in instruction.get("Actions", [])
        ):
            continue
        if state in ("Sleep", "BreedPair") and not any(
            action.get("Type") == "TameworkSetFlyingCompanionMode"
            and action.get("Mode") == "Hold"
            and action.get("LandingState") == state
            and action.get("GroundedState") == state
            for instruction in descendants(instruction_children(branch))
            for action in instruction.get("Actions", [])
        ):
            continue
        return True
    return False


def check_wild_shared() -> None:
    require(WILD_COMPONENT.exists(), f"missing {WILD_COMPONENT.relative_to(ROOT)}")
    component = load(WILD_COMPONENT)
    require(component.get("Interface") == "AnimalHusbandry.Instruction.AerialFollowItem", "wrong wild interface")
    component_text = text(WILD_COMPONENT)
    for token in ("ItemInHand", "TakeOff", "Land", "MaintainDistance"):
        require(token in component_text, f"wild component missing {token}")
    instructions = component.get("Content", {}).get("Instructions", [])
    require(
        any(
            action.get("Type") == "State" and action.get("State") == "FollowItemGrounded"
            for instruction in instructions
            for action in instruction.get("Actions", [])
        ),
        "wild component has no State action targeting FollowItemGrounded",
    )
    require(
        has_target_loss_branch(instructions, "FollowItem", "Walk", ["ReleaseTarget", "State"]),
        "wild component has no FollowItem + Walk target-loss ReleaseTarget/Idle branch",
    )
    require(
        has_target_loss_branch(instructions, "FollowItem", "Fly", ["ReleaseTarget", "State"]),
        "wild component has no FollowItem + Fly target-loss ReleaseTarget/Idle branch",
    )
    require(
        has_target_loss_branch(instructions, "FollowItemLanding", "Walk", ["ReleaseTarget", "TakeOff", "State"]),
        "wild component has no FollowItemLanding + Walk target-loss release/takeoff/Idle branch",
    )
    require(
        has_target_loss_branch(instructions, "FollowItemGrounded", "Walk", ["ReleaseTarget", "TakeOff", "State"]),
        "wild component has no FollowItemGrounded + Walk target-loss release/takeoff/Idle branch",
    )
    template_text = text(WILD_TEMPLATE)
    require("AH_Component_Tamework_Instruction_Aerial_Follow_Item" in template_text, "wild template does not consume attraction component")
    for state in ("FollowItem", "FollowItemLanding", "FollowItemGrounded"):
        require(state in template_text, f"wild template missing state {state}")


def check_tamed_shared() -> None:
    require(MODE_COMPONENT.exists(), f"missing {MODE_COMPONENT.relative_to(ROOT)}")
    component = load(MODE_COMPONENT)
    require(component.get("Type") == "Component", "mode component must be a Component")
    require(component.get("Class") == "Instruction", "mode component must be an Instruction")
    require(component.get("Interface") == "AnimalHusbandry.Instruction.AerialModeTransition", "wrong mode interface")
    content = component.get("Content", {})
    require(content.get("Continue") is True, "mode component content must continue")
    require(content.get("Sensor", {}).get("Type") == "Any", "mode component content must use Any")
    mode_instructions = content.get("Instructions", [])
    require(mode_instructions, "mode component has no instructions")
    hook = mode_instructions[0]
    require(
        hook.get("Sensor", {}).get("Type") == "TameworkHook"
        and hook.get("Sensor", {}).get("HookId") == HOOK_ID
        and hook.get("Sensor", {}).get("Consume") is True,
        "mode component must first consume ToggleAirborneMode",
    )
    require(
        any(
            instruction.get("Sensor", {}).get("Type") == "Flag"
            and instruction.get("Sensor", {}).get("Name") == "AirborneMode"
            and "Set" not in instruction.get("Sensor", {})
            and any(
                action.get("Type") == "SetFlag"
                and action.get("Name") == "AirborneMode"
                and action.get("SetTo") is False
                for action in instruction.get("Actions", [])
            )
            for instruction in instruction_children(hook)
        ),
        "mode component missing AirborneMode true-to-false branch",
    )
    require(
        any(
            instruction.get("Sensor", {}).get("Type") == "Flag"
            and instruction.get("Sensor", {}).get("Name") == "AirborneMode"
            and instruction.get("Sensor", {}).get("Set") is False
            and any(
                action.get("Type") == "SetFlag"
                and action.get("Name") == "AirborneMode"
                and action.get("SetTo") is True
                for action in instruction.get("Actions", [])
            )
            for instruction in instruction_children(hook)
        ),
        "mode component missing AirborneMode false-to-true branch",
    )
    require(
        has_body_motion_branch(
            mode_instructions,
            {"AirborneMode": None, "AerialGroundedActivity": False},
            "Walk",
            "TakeOff",
            JumpSpeed=4,
        )
        and has_action(mode_instructions, "PlayAnimation", Slot="Status"),
        "mode component missing gated Walk TakeOff",
    )
    landing_branch = next(
        (
            instruction
            for instruction in descendants(mode_instructions)
            if instruction.get("Sensor", {}).get("Type") == "And"
            and has_flag(instruction.get("Sensor", {}).get("Sensors", []), "AirborneMode", False)
            and has_controller(instruction.get("Sensor", {}).get("Sensors", []), "Fly")
        ),
        None,
    )
    require(landing_branch is not None, "mode component missing Fly landing conjunction")
    require(
        any(
            child.get("Sensor", {}).get("Type") == "AdjustPosition"
            and child.get("Sensor", {}).get("Offset") == [0, 1, 0]
            and child.get("Sensor", {}).get("Sensor", {}).get("Type") == "SearchRay"
            and child.get("Sensor", {}).get("Sensor", {}).get("Name") == "AH_Aerial_Mode_LandingRay"
            and child.get("Sensor", {}).get("Sensor", {}).get("Range") == 64
            and child.get("Sensor", {}).get("Sensor", {}).get("Angle") == 90
            and child.get("Sensor", {}).get("Sensor", {}).get("Blocks") == "StoneAndSoil"
            and child.get("BodyMotion", {}).get("Type") == "Land"
            and child.get("BodyMotion", {}).get("SlowDownDistance") == 5
            and child.get("BodyMotion", {}).get("StopDistance") == 0.5
            and child.get("BodyMotion", {}).get("HeightDifference") == [-3, 2]
            and child.get("BodyMotion", {}).get("GoalLenience") == 3
            and child.get("BodyMotion", {}).get("DesiredAltitudeWeight") == 0
            for child in instruction_children(landing_branch)
        ),
        "mode component missing configured landing ray/Land",
    )
    require(
        has_conjunction(mode_instructions, {"AirborneMode": False}, "Walk")
        and has_action(mode_instructions, "ResetSearchRays"),
        "mode component missing Walk touchdown ray reset",
    )
    template = load(TAMED_TEMPLATE)
    require(template.get("StartState") == "Idle", "tamed template must start Idle")
    require(template.get("InitialMotionController") == "Walk", "tamed template must start Walk")
    require(has_initial_flag(template, "AirborneMode", False), "tamed template must initialize AirborneMode=false")
    template_text = text(TAMED_TEMPLATE)
    require("AH_Component_Tamework_Instruction_Aerial_Mode_Transition" in template_text, "tamed template missing mode transition")
    mode_reference = next(
        (
            instruction
            for instruction in template.get("Instructions", [])
            if instruction.get("Reference") == "AH_Component_Tamework_Instruction_Aerial_Mode_Transition"
        ),
        None,
    )
    require(mode_reference is not None and mode_reference.get("Continue") is True, "mode transition must be global Continue")
    require(has_state_action(template, "Idle", "TameworkSetFlyingCompanionMode", Mode="Follow"), "Idle entry must clear landing mode")
    require(
        has_body_motion_branch(template.get("Instructions", []), {"AirborneMode": False}, "Walk", "WanderInCircle")
        and has_body_motion_branch(template.get("Instructions", []), {"AirborneMode": None}, "Fly", "WanderInCircle"),
        "Idle must provide Walk and Fly wander modes",
    )
    require(
        has_state_mode_reference(template, "Follow", {"AirborneMode": False}, "Walk", "Component_Tamework_Instruction_Follow_Advanced")
        and has_state_mode_reference(template, "Follow", {"AirborneMode": None}, "Fly", "AH_Component_Tamework_Instruction_Follow_Flying"),
        "Follow must provide Walk and Fly mode references",
    )
    require(
        has_body_motion_branch(template.get("Instructions", []), {"AirborneMode": False}, "Walk", "Nothing")
        and has_state_mode_action(template, "Hold", {"AirborneMode": None}, "Fly", "TameworkSetFlyingCompanionMode", Mode="Follow")
        and has_body_motion_branch(template.get("Instructions", []), {"AirborneMode": None}, "Fly", "Nothing"),
        "Hold must provide grounded and airborne stationary modes",
    )
    require(
        not has_reference(
            [branch for branch in state_branches(template, "Hold")],
            "AH_Component_Tamework_Instruction_Hold_Flying",
        ),
        "airborne Hold must not run the landing-oriented Hold_Flying component",
    )
    for state in ("Sleep", "BreedPair", "NeedsSeekWater", "NeedsSeekFood"):
        require(has_activity_wrapper(template, state), f"{state} missing grounded activity wrapper")
    require(has_grounded_activity_release(template), "grounded activity flag must clear after husbandry state exits")
    needs = {
        instruction.get("Modify", {}).get("NeedsSeekResourceType"): instruction.get("Modify", {})
        for instruction in descendants(template.get("Instructions", []))
        if instruction.get("Reference") == "Component_Tamework_Instruction_Needs_Seek_Resource"
    }
    require(
        needs.get("Water", {}).get("NeedsSeekFlyingLandingEnabled") is True
        and needs.get("Water", {}).get("NeedsSeekFlyingLandingState") == "NeedsSeekWater"
        and needs.get("FoodContainer", {}).get("NeedsSeekFlyingLandingEnabled") is True
        and needs.get("FoodContainer", {}).get("NeedsSeekFlyingLandingState") == "NeedsSeekFood",
        "needs-seek water/food landing fields must remain enabled and state-matched",
    )
    for reference in (
        "Component_ActionList_Sleep",
        "Component_ActionList_Wake",
        "Component_Instruction_Damage_Check",
        "Component_Instruction_Leash_To_Flock_Leader",
        "Component_Instruction_Wild_Sleep_State",
        "Component_Sensor_Standard_Detection",
        "Component_Tamework_Instruction_Breeding_Pair",
        "Component_Tamework_Instruction_Command_Move",
        "Component_Tamework_Instruction_Defend",
        "Component_Tamework_Instruction_Needs_Seek_Resource",
        "Component_Tamework_Instruction_Needs_Seek_Resource_Sensor",
        "Component_Tamework_Instruction_SeekFood_PlayerFollow",
        "AH_Component_Tamework_Instruction_Follow_Flying",
        "AH_Component_Tamework_Instruction_Hold_Flying",
    ):
        require(contains_reference(template, reference), f"tamed template lost existing reference {reference}")
    for key, expected in (("CanDefend", False), ("CanAttackTarget", False), ("AttackWhenStartled", False)):
        require(template.get("Parameters", {}).get(key, {}).get("Value") is expected, f"tamed combat parameter {key} must remain false")
    require(template.get("Parameters", {}).get("Attack", {}).get("Value") == "", "tamed Attack parameter must remain empty")
    if TAMED_VARIANT_ROOT.exists():
        for variant in sorted(TAMED_VARIANT_ROOT.glob("*.json")):
            document = load(variant)
            modify = document.get("Modify", {})
            require(modify.get("CanDefend") is False, f"{variant.name} enables CanDefend")
            require(modify.get("CanAttackTarget") is False, f"{variant.name} enables CanAttackTarget")


SCOPES = {"wild-shared": check_wild_shared, "tamed-shared": check_tamed_shared}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--scope", choices=sorted(SCOPES), required=True)
    args = parser.parse_args()
    SCOPES[args.scope]()
