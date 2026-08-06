from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
BASELINE_COMMIT = "0fa7f94"
HOOK_ID = "AnimalHusbandry.Command.ToggleAirborneMode"
LOCAL_WILD_COMPONENT = ROOT / "Server/NPC/Roles/_Core/Components/AH_Component_Tamework_Instruction_Aerial_Follow_Item.json"
LOCAL_MODE_COMPONENT = ROOT / "Server/NPC/Roles/_Core/Components/AH_Component_Tamework_Instruction_Aerial_Mode_Transition.json"
LOCAL_HOLD_COMPONENT = ROOT / "Server/NPC/Roles/_Core/Components/AH_Component_Tamework_Instruction_Hold_Flying.json"
LOCAL_FROST_MODE_COMPONENT = ROOT / "Server/NPC/Roles/Creature/Mythic/Components/Component_AH_Instruction_Dragon_Frost_Airborne_Mode_Transition.json"
LOCAL_FLYING_FOLLOW_COMPONENT = ROOT / "Server/NPC/Roles/_Core/Components/AH_Component_Tamework_Instruction_Follow_Flying.json"
LOCAL_LARGE_FOLLOW_COMPONENT = ROOT / "Server/NPC/Roles/_Core/Components/AH_Component_Tamework_Instruction_Follow_Large.json"
FROST_FLYING_FOLLOW_COMPONENT = ROOT / "Server/NPC/Roles/_Core/Components/AH_Component_Tamework_Instruction_Follow_Frost_Dragon_Flying.json"
WILD_TEMPLATE = ROOT / "Server/NPC/Roles/_Core/Templates/AH_Template_Aerial_Neutral.json"
TAMED_TEMPLATE = ROOT / "Server/NPC/Roles/_Core/Templates/AH_Template_Aerial_Tamed.json"
FROST_DRAGON_TEMPLATE = ROOT / "Server/NPC/Roles/_Core/Templates/AH_Template_Dragon_Frost_Tamed.json"
FROST_DRAGON_ROLE = ROOT / "Server/NPC/Roles/Creature/Mythic/Tamed/Tamed_Dragon_Frost.json"
INTERACTION_CONFIG = ROOT / "Server/Tamework/Interactions/AHIntNeutral.json"
TAMED_VARIANT_ROOT = ROOT / "Server/NPC/Roles/Avian/Aerial/Tamed"

SPECIES = {
    "Bluebird": ("Avian/Aerial", "Drop_Bluebird", 15, 15, "Bluebird", "Plant_Crop_Corn_Item", "Want_Food_Corn", ("Tw_Feed_Herbivore",)),
    "Sparrow": ("Avian/Aerial", "Drop_Sparrow", 15, 15, None, "Plant_Crop_Corn_Item", "Want_Food_Corn", ("Tw_Feed_Herbivore",)),
    "Parrot": ("Avian/Aerial", "Drop_Parrot", 12, 29, None, "Plant_Fruit_Apple", "Want_Food_Apple", ("Tw_Feed_Herbivore",)),
    "Raven": ("Avian/Aerial", "Drop_Raven", 15, 49, None, "Plant_Crop_Corn_Item", "Want_Food_Corn", ("Tw_Feed_Herbivore", "Tw_Feed_Carnivore")),
    "Crow": ("Avian/Aerial", "Drop_Crow", 15, 20, None, "Plant_Crop_Corn_Item", "Want_Food_Corn", ("Tw_Feed_Herbivore", "Tw_Feed_Carnivore")),
    "Finch_Green": ("Avian/Aerial", "Drop_Finch_Green", 15, 15, "Finch_Green", "Plant_Crop_Corn_Item", "Want_Food_Corn", ("Tw_Feed_Herbivore",)),
    "Woodpecker": ("Avian/Aerial", "Drop_Woodpecker", 15, 15, None, "Plant_Crop_Corn_Item", "Want_Food_Corn", ("Tw_Feed_Herbivore", "Tw_Feed_Carnivore")),
    "Owl_Brown": ("Avian/Aerial", "Drop_Owl_Brown", 12, 29, "Owl_Brown", "Food_Wildmeat_Raw", "Want_Food_Wildmeat_Raw", ("Tw_Feed_Carnivore",)),
    "Owl_Snow": ("Avian/Aerial", "Drop_Owl_Snow", 12, 29, None, "Food_Wildmeat_Raw", "Want_Food_Wildmeat_Raw", ("Tw_Feed_Carnivore",)),
    "Bat": ("Avian/Aerial", "Drop_Bat", 15, 15, None, "Plant_Fruit_Apple", "Want_Food_Apple", ("Tw_Feed_Herbivore",)),
    "Bat_Ice": ("Avian/Aerial", "Drop_Bat_Ice", 15, 25, None, "Plant_Fruit_Apple", "Want_Food_Apple", ("Tw_Feed_Herbivore",)),
}

SPECIES.update({
    "Pigeon": ("Avian/Fowl", "Drop_Pigeon", 15, 20, None, "Plant_Crop_Corn_Item", "Want_Food_Corn", ("Tw_Feed_Herbivore",)),
    "Duck": ("Avian/Fowl", "Drop_Duck", 15, 25, "Duck", "Plant_Crop_Corn_Item", "Want_Food_Corn", ("Tw_Feed_Herbivore", "Tw_Feed_Carnivore")),
    "Archaeopteryx": ("Avian/Raptor", "Drop_Archaeopteryx", 15, 61, None, "Food_Wildmeat_Raw", "Want_Food_Wildmeat_Raw", ("Tw_Feed_Carnivore",)),
    "Hawk": ("Avian/Raptor", "Drop_Hawk", 15, 38, None, "Food_Wildmeat_Raw", "Want_Food_Wildmeat_Raw", ("Tw_Feed_Carnivore",)),
    "Pterodactyl": ("Avian/Raptor", "Drop_Pterodactyl", 25, 60, None, "Food_Wildmeat_Raw", "Want_Food_Wildmeat_Raw", ("Tw_Feed_Carnivore",)),
    "Vulture": ("Avian/Raptor", "Drop_Vulture", 30, 61, None, "Food_Wildmeat_Raw", "Want_Food_Wildmeat_Raw", ("Tw_Feed_Carnivore",)),
})

TAMED_IDS = tuple(f"Tamed_{name}" for name in SPECIES)
OMNIVORE_IDS = {"Tamed_Crow", "Tamed_Raven", "Tamed_Duck", "Tamed_Woodpecker"}
CARNIVORE_IDS = {
    "Tamed_Archaeopteryx",
    "Tamed_Hawk",
    "Tamed_Owl_Brown",
    "Tamed_Owl_Snow",
    "Tamed_Pterodactyl",
    "Tamed_Vulture",
}


def load(path: Path) -> dict:
    with path.open(encoding="utf-8-sig") as handle:
        return json.load(handle)


def text(path: Path) -> str:
    return path.read_text(encoding="utf-8-sig")


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def nested(document: dict, keys: tuple[str, ...]) -> object:
    value: object = document
    for key in keys:
        require(isinstance(value, dict) and key in value, f"missing {key} while reading config membership")
        value = value[key]
    return value


def members(relative: str, *keys: str) -> list[str]:
    value = nested(load(ROOT / relative), keys)
    require(isinstance(value, list) and all(isinstance(item, str) for item in value), f"invalid membership list in {relative}")
    return value


def baseline_load(relative: str) -> dict:
    try:
        payload = subprocess.check_output(
            ["git", "show", f"{BASELINE_COMMIT}:{relative}"],
            cwd=ROOT,
        )
    except (OSError, subprocess.CalledProcessError) as error:
        raise AssertionError(f"cannot load baseline {BASELINE_COMMIT}:{relative}: {error}") from error
    return json.loads(payload.decode("utf-8-sig"))


def canonical_sha(value: object) -> str:
    encoded = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def baseline_members(relative: str, *keys: str) -> list[str]:
    value = nested(baseline_load(relative), keys)
    require(isinstance(value, list) and all(isinstance(item, str) for item in value), f"invalid baseline membership list in {relative}")
    return value


def check_membership(
    relative: str,
    keys: tuple[str, ...],
    feature_ids: set[str],
    expected_feature_ids: set[str],
    label: str,
) -> None:
    current = members(relative, *keys)
    require(len(current) == len(set(current)), f"{label} contains duplicate IDs")
    require(set(current) & feature_ids == expected_feature_ids, f"{label} feature-ID intersection drift")
    baseline = baseline_members(relative, *keys)
    current_unrelated = [item for item in current if item not in feature_ids]
    baseline_unrelated = [item for item in baseline if item not in feature_ids]
    require(
        len(current_unrelated) == len(baseline_unrelated)
        and canonical_sha(current_unrelated) == canonical_sha(baseline_unrelated),
        f"{label} unrelated baseline drift",
    )


def check_non_role_content(relative: str) -> None:
    current = load(ROOT / relative)
    baseline = baseline_load(relative)
    current.pop("RoleIds", None)
    baseline.pop("RoleIds", None)
    require(canonical_sha(current) == canonical_sha(baseline), f"{relative} non-RoleIds content drift")


def has_item_target_loss_sensor(sensor: dict) -> bool:
    if sensor.get("Type") != "Not":
        return False
    target = sensor.get("Sensor", {})
    if target.get("Type") != "Target":
        return False
    target_slot = target.get("TargetSlot")
    if not isinstance(target_slot, dict) or target_slot.get("Compute") != "FollowTargetSlot":
        return False
    filters = target.get("Filters")
    if not isinstance(filters, list):
        return False
    return any(
        isinstance(filter_entry, dict)
        and filter_entry.get("Type") == "ItemInHand"
        and isinstance(filter_entry.get("Items"), dict)
        and filter_entry["Items"].get("Compute") == "AttractiveItemSet"
        for filter_entry in filters
    )


def has_target_loss_branch(
    instructions: list[dict],
    state: str,
    controller: str,
    action_types: list[str],
    take_off: bool = False,
) -> bool:
    for instruction in instructions:
        outer_sensor = instruction.get("Sensor", {})
        if outer_sensor.get("Type") != "And":
            continue
        sensors = outer_sensor.get("Sensors", [])
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
        if not actions or actions[0].get("TargetSlot", {}).get("Compute") != "FollowTargetSlot":
            continue
        if actions[-1].get("Type") != "ParentState" or actions[-1].get("State") != "Idle":
            continue
        body_motion = instruction.get("BodyMotion", {})
        if take_off != (body_motion.get("Type") == "TakeOff" and body_motion.get("JumpSpeed") == 4):
            continue
        if take_off and actions[-1].get("ClearBodyMotion") is not False:
            continue
        return True
    return False


def object_nodes(value: object) -> list[dict]:
    nodes: list[dict] = []
    if isinstance(value, dict):
        nodes.append(value)
        for child in value.values():
            nodes.extend(object_nodes(child))
    elif isinstance(value, list):
        for child in value:
            nodes.extend(object_nodes(child))
    return nodes


def instruction_children(instruction: dict) -> list[dict]:
    children = instruction.get("Instructions", [])
    return children if isinstance(children, list) else []


def descendants(instructions: list[dict]) -> list[dict]:
    result: list[dict] = []
    for instruction in instructions:
        result.append(instruction)
        result.extend(descendants(instruction_children(instruction)))
    return result


def has_favorite_item_filter(value: object) -> bool:
    return any(
        node.get("Type") == "ItemInHand"
        and node.get("Items", {}).get("Compute") == "AttractiveItemSet"
        for node in object_nodes(value)
    )


def has_slow_ground_controller(template: dict) -> bool:
    parameters = template.get("Parameters", {})
    ground_speed = parameters.get("GroundSpeed", {}).get("Value")
    controllers = template.get("MotionControllerList", [])
    fly = next((controller for controller in controllers if controller.get("Type") == "Fly"), {})
    walk = next((controller for controller in controllers if controller.get("Type") == "Walk"), {})
    return (
        isinstance(ground_speed, (int, float))
        and 0 < ground_speed <= 3
        and fly.get("MaxHorizontalSpeed", {}).get("Compute") == "MaxSpeed"
        and walk.get("MaxWalkSpeed", {}).get("Compute") == "GroundSpeed"
    )


def favorite_item_preempts_proximity_flee(template: dict) -> bool:
    alerted = state_branches(template, "Alerted")
    if len(alerted) != 1:
        return False
    instructions = instruction_children(alerted[0])
    favorite_indices = [
        index
        for index, instruction in enumerate(instructions)
        if has_favorite_item_filter(instruction.get("Sensor", {}))
    ]
    proximity_flee_indices = [
        index
        for index, instruction in enumerate(instructions)
        if instruction.get("BodyMotion", {}).get("Type") == "Flee"
    ]
    return (
        len(favorite_indices) == 1
        and bool(proximity_flee_indices)
        and favorite_indices[0] < min(proximity_flee_indices)
    )


def favorite_item_uses_full_alerted_range(template: dict) -> bool:
    alerted = state_branches(template, "Alerted")
    if len(alerted) != 1:
        return False
    favorite = [
        instruction
        for instruction in instruction_children(alerted[0])
        if has_favorite_item_filter(instruction.get("Sensor", {}))
    ]
    parameters = template.get("Parameters", {})
    alerted_range = parameters.get("AlertedRange", {}).get("Value")
    action_range = parameters.get("AlertedActionRange", {}).get("Value")
    return (
        len(favorite) == 1
        and favorite[0].get("Sensor", {}).get("Range", {}).get("Compute") == "AlertedRange"
        and isinstance(alerted_range, (int, float))
        and isinstance(action_range, (int, float))
        and alerted_range > action_range
    )


def aerial_defaults_are_declared(template: dict, expected: dict[str, object]) -> bool:
    parameters = template.get("Parameters", {})
    return (
        all(parameters.get(name, {}).get("Value") == value for name, value in expected.items())
        and not any(name in template for name in expected)
    )


def aerial_ground_follow_matches_critters(template: dict) -> bool:
    references = reference_nodes(template, "Component_Tamework_Instruction_Follow_Advanced")
    expected = {
        "MasterTargetSlot": "MasterTarget",
        "FollowDefaultSpotRange": 5,
        "FollowLockOnRange": 15,
        "FollowSeekSlowDownDistance": 5,
        "FollowSeekStopDistance": 3,
        "FollowScanRange": 10,
        "FollowMaintainDistanceRange": [1, 4],
    }
    return len(references) == 1 and references[0].get("Modify") == expected


def state_branches(template: dict, state: str) -> list[dict]:
    return [
        instruction
        for instruction in descendants(template.get("Instructions", []))
        if instruction.get("Sensor", {}).get("Type") == "State"
        and instruction.get("Sensor", {}).get("State") == state
    ]


def reference_state_ancestors(document: object, reference: str, ancestors: tuple[str, ...] = ()) -> list[tuple[str, ...]]:
    """Return state-sensor ancestry for every matching instruction reference."""
    matches: list[tuple[str, ...]] = []
    if isinstance(document, dict):
        sensor = document.get("Sensor")
        current = ancestors
        if isinstance(sensor, dict) and sensor.get("Type") == "State":
            state = sensor.get("State")
            if isinstance(state, str):
                current = ancestors + (state,)
        if document.get("Reference") == reference:
            matches.append(current)
        for key, value in document.items():
            if key == "Sensor":
                continue
            matches.extend(reference_state_ancestors(value, reference, current))
    elif isinstance(document, list):
        for value in document:
            matches.extend(reference_state_ancestors(value, reference, ancestors))
    return matches


def reference_nodes(document: object, reference: str) -> list[dict]:
    """Return matching instruction dictionaries without relying on source text."""
    matches: list[dict] = []
    if isinstance(document, dict):
        if document.get("Reference") == reference:
            matches.append(document)
        for key, value in document.items():
            if key == "Sensor":
                continue
            matches.extend(reference_nodes(value, reference))
    elif isinstance(document, list):
        for value in document:
            matches.extend(reference_nodes(value, reference))
    return matches


def has_favorite_target_sensor(sensor: object) -> bool:
    if not isinstance(sensor, dict) or sensor.get("Type") != "Target":
        return False
    target_slot = sensor.get("TargetSlot")
    if not isinstance(target_slot, dict) or target_slot.get("Compute") != "FollowTargetSlot":
        return False
    filters = sensor.get("Filters")
    if not isinstance(filters, list):
        return False
    return any(
        isinstance(filter_entry, dict)
        and filter_entry.get("Type") == "ItemInHand"
        and isinstance(filter_entry.get("Items"), dict)
        and filter_entry["Items"].get("Compute") == "AttractiveItemSet"
        for filter_entry in filters
    )


def has_first_sensor_branch(
    instructions: list[dict],
    predicate: object,
    sensor_type: str,
    slot_key: str,
    slot_compute: str,
    favorite_target: bool = False,
) -> bool:
    for instruction in descendants(instructions):
        if not predicate(instruction):
            continue
        outer_sensor = instruction.get("Sensor", {})
        if outer_sensor.get("Type") != "And":
            continue
        sensors = outer_sensor.get("Sensors", [])
        if not sensors or sensors[0].get("Type") != sensor_type:
            continue
        if sensors[0].get(slot_key, {}).get("Compute") != slot_compute:
            continue
        if favorite_target and not has_favorite_target_sensor(sensors[0]):
            continue
        return True
    return False


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


def is_state_controller_conjunction(sensor: dict, state: str, controller: str) -> bool:
    if sensor.get("Type") != "And":
        return False
    sensors = sensor.get("Sensors", [])
    return any(
        entry.get("Type") == "State" and entry.get("State") == state
        for entry in sensors
    ) and has_controller(sensors, controller)


def has_activity_controller_boundary(template: dict, state: str) -> bool:
    """Require direct top-level Fly/Walk gates before the activity component."""
    instructions = template.get("Instructions", [])
    fly_indexed = [
        (index, instruction)
        for index, instruction in enumerate(instructions)
        if is_state_controller_conjunction(
            instruction.get("Sensor", {}), state, "Fly"
        )
    ]
    walk_indexed = [
        (index, instruction)
        for index, instruction in enumerate(instructions)
        if is_state_controller_conjunction(
            instruction.get("Sensor", {}), state, "Walk"
        )
    ]
    if not fly_indexed or not walk_indexed:
        return False
    fly_index, fly = fly_indexed[0]
    walk_index, walk = walk_indexed[0]
    if fly.get("Continue") is not False or walk.get("Continue") is not True:
        return False
    if not any(
        action.get("Type") == "TameworkSetFlyingCompanionMode"
        and action.get("Mode") == "Hold"
        and action.get("LandingState") == state
        and action.get("GroundedState") == state
        for action in fly.get("Actions", [])
    ):
        return False
    if not any(
        action.get("Type") == "SetFlag"
        and action.get("Name") == "AerialGroundedActivity"
        and action.get("SetTo") is True
        for action in walk.get("Actions", [])
    ):
        return False
    if fly_index >= walk_index:
        return False
    activity_references = (
        ("Component_Tamework_Instruction_Breeding_Pair",)
        if state == "BreedPair"
        else ("Component_ActionList_Sleep", "Component_Instruction_Wild_Sleep_State")
    )
    activity_indices = [
        index
        for index, instruction in enumerate(instructions)
        if any(contains_reference(instruction, reference) for reference in activity_references)
    ]
    if not activity_indices:
        return False
    return walk_index < min(activity_indices)


def has_state_controller_instruction(template: dict, state: str, controller: str) -> bool:
    return any(
        is_state_controller_conjunction(
            instruction.get("Sensor", {}), state, controller
        )
        for instruction in descendants(template.get("Instructions", []))
    )


def check_wild_shared() -> None:
    require(
        not LOCAL_WILD_COMPONENT.exists(),
        "local flying favorite-item component must move to Tamework",
    )
    template = load(WILD_TEMPLATE)
    require(
        has_slow_ground_controller(template),
        "wild Walk controller must use a dedicated GroundSpeed no faster than 3",
    )
    require(
        aerial_defaults_are_declared(
            template,
            {
                "FoodBlockSet": "Hay",
                "GrazingBlockSet": "Grass",
                "DayTimeNapWeight": 0,
                "NeedsSeekConsumeAnimation": "",
                "SleepAnimation": "",
                "SleepEnterAnimation": "",
                "WakeAnimation": "",
                "CuriousAnimation": "",
                "AlertedAnimation": "FlyFast",
            },
        ),
        "wild aerial defaults must be declared parameters rather than unknown root attributes",
    )
    require(
        favorite_item_preempts_proximity_flee(template),
        "wild favorite-item acquisition must precede the Alerted proximity-flee branch",
    )
    require(
        favorite_item_uses_full_alerted_range(template),
        "wild favorite-item acquisition must use the full AlertedRange",
    )
    reference = "Component_Tamework_Instruction_SeekFood_PlayerFollow_Flying"
    matches = reference_nodes(template, reference)
    ancestors = reference_state_ancestors(template, reference)
    require(len(matches) == 1, "wild template must consume attraction component exactly once")
    require(ancestors == [("FollowItem",)], "wild attraction component reference must be scoped to FollowItem")
    require(
        matches[0].get("Modify") == {
            "AttractiveItemSet": {"Compute": "AttractiveItemSet"},
            "FollowTargetSlot": "LockedTarget",
            "LandingPositionSlot": "AH_Aerial_Favorite_Landing",
            "FlightSeekStopDistance": 5.0,
            "GroundApproachDistanceRange": [1.5, 2.0],
            "_ExportStates": ["Idle"],
        },
        "wild attraction component must preserve all aerial favorite-item tuning",
    )


def check_tamed_shared() -> None:
    require(
        not LOCAL_MODE_COMPONENT.exists(),
        "local airborne-mode transition must move to Tamework",
    )
    require(
        not LOCAL_HOLD_COMPONENT.exists(),
        "local flying Hold component must move to Tamework",
    )
    template = load(TAMED_TEMPLATE)
    require(
        has_slow_ground_controller(template),
        "tamed Walk controller must use a dedicated GroundSpeed no faster than 3",
    )
    require(
        aerial_defaults_are_declared(
            template,
            {
                "NeedsSeekConsumeStartDistance": 2.25,
                "FoodBlockSet": "Livestock_Feeding",
                "GrazingBlockSet": "Grass",
                "DayTimeNapWeight": 0,
                "GreetAnimation": "",
            },
        ),
        "tamed aerial defaults must be declared parameters rather than unknown root attributes",
    )
    require(template.get("StartState") == "Idle", "tamed template must start Idle")
    require(template.get("InitialMotionController") == "Walk", "tamed template must start Walk")
    require(
        not has_initial_flag(template, "AirborneMode", False),
        "AirborneMode must use its default false value so state changes cannot reset the selected flight mode",
    )
    template_text = text(TAMED_TEMPLATE)
    require("Component_Tamework_Instruction_Airborne_Mode_Transition" in template_text, "tamed template missing mode transition")
    mode_reference = next(
        (
            instruction
            for instruction in template.get("Instructions", [])
            if instruction.get("Reference") == "Component_Tamework_Instruction_Airborne_Mode_Transition"
        ),
        None,
    )
    require(mode_reference is not None and mode_reference.get("Continue") is True, "mode transition must be global Continue")
    require(
        mode_reference.get("Modify") == {
            "ToggleAirborneModeHookId": "AnimalHusbandry.Command.ToggleAirborneMode",
            "AirborneModeFlagName": "AirborneMode",
            "GroundedActivityFlagName": "AerialGroundedActivity",
            "LandingRayName": "AH_Aerial_Mode_LandingRay",
            "LandingBlocks": "StoneAndSoil",
            "LandingSearchRange": 64,
            "LandingSearchAngle": 90,
            "LandingSlowDownDistance": 5,
            "LandingStopDistance": 0.5,
            "LandingHeightDifference": [-3, 2],
            "LandingGoalLenience": 3,
            "LandingDesiredAltitudeWeight": 0,
        },
        "tamed mode transition must preserve hook, flags, ray, and landing tuning",
    )
    for state in ("Idle", "Follow", "Hold"):
        require(
            not has_state_action(template, state, "TameworkSetFlyingCompanionMode"),
            f"{state} must preserve the selected airborne mode instead of resetting Tamework flight state",
        )
    require(
        has_body_motion_branch(template.get("Instructions", []), {"AirborneMode": False}, "Walk", "WanderInCircle")
        and has_body_motion_branch(template.get("Instructions", []), {"AirborneMode": None}, "Fly", "WanderInCircle"),
        "Idle must provide Walk and Fly wander modes",
    )
    require(
        has_state_mode_reference(template, "Follow", {"AirborneMode": False}, "Walk", "Component_Tamework_Instruction_Follow_Advanced")
        and has_state_mode_reference(template, "Follow", {"AirborneMode": None}, "Fly", "Component_Tamework_Instruction_Follow_Flying"),
        "Follow must provide Walk and Fly mode references",
    )
    require(
        aerial_ground_follow_matches_critters(template),
        "grounded aerial Follow must use the standard critter follow distances",
    )
    flying_follow_references = reference_nodes(template, "Component_Tamework_Instruction_Follow_Flying")
    require(len(flying_follow_references) == 1, "tamed template must consume flying follow exactly once")
    require(
        flying_follow_references[0].get("Modify") == {
            "MasterTargetSlot": "MasterTarget",
            "FollowDesiredAltitudeRange": [6, 10],
            "FollowTeleportThresholdRange": 32,
            "FollowOrbitRadiusRange": [16, 24],
            "FollowOrbitRetargetTimeRange": [3, 6],
            "FollowOrbitStopDistance": 3,
            "FollowOrbitRelativeSpeed": 0.65,
            "FollowHoverRadius": 1.75,
            "FollowHoverRelativeSpeed": 0.12,
        },
        "shared flying follow must preserve all Animal Husbandry tuning explicitly",
    )
    favorite_particle_actions = [
        node
        for node in object_nodes(template.get("Instructions", []))
        if node.get("Type") == "SpawnParticles"
        and node.get("ParticleSystem") == {"Compute": "AttractiveItemSetParticles"}
    ]
    require(favorite_particle_actions, "tamed template has no favorite-item particle action")
    require(
        all(
            action.get("Enabled", {}).get("Compute") == "!isEmpty(AttractiveItemSetParticles)"
            for action in favorite_particle_actions
        ),
        "favorite-item particle actions must be disabled when the particle ID is empty",
    )
    for need, particle_parameter, timer_name in (
        ("Hunger", "AttractiveItemSetParticles", "Hunger_FoodThought_Cooldown"),
        ("Thirst", "WaterThoughtParticles", "Thirst_WaterThought_Cooldown"),
    ):
        thought_branches = [
            instruction
            for instruction in descendants(template.get("Instructions", []))
            if any(
                node.get("Type") == "TameworkNeedBelow" and node.get("Need") == need
                for node in object_nodes(instruction.get("Sensor", {}))
            )
            and any(
                action.get("Type") == "SpawnParticles"
                and action.get("ParticleSystem") == {"Compute": particle_parameter}
                for action in instruction.get("Actions", [])
            )
            and any(
                action.get("Type") == "TimerStart" and action.get("Name") == timer_name
                for action in instruction.get("Actions", [])
            )
        ]
        require(len(thought_branches) == 1, f"tamed template missing {need.lower()} thought-bubble branch")
    require(
        has_body_motion_branch(template.get("Instructions", []), {"AirborneMode": False}, "Walk", "Nothing")
        and has_body_motion_branch(template.get("Instructions", []), {"AirborneMode": None}, "Fly", "Nothing"),
        "Hold must provide grounded and airborne stationary modes",
    )
    require(
        not has_reference(
            [branch for branch in state_branches(template, "Hold")],
            "Component_Tamework_Instruction_Hold_Flying",
        ),
        "airborne Hold must not run the landing-oriented Hold_Flying component",
    )
    for state in ("NeedsSeekWater", "NeedsSeekFood"):
        require(has_activity_wrapper(template, state), f"{state} missing grounded activity wrapper")
    for state in ("Sleep", "BreedPair"):
        require(
            has_activity_controller_boundary(template, state),
            f"{state} activity requires direct top-level Fly blocker and Walk release before activity",
        )
    require(
        has_state_controller_instruction(template, "Sleep", "Walk"),
        "Sleep body must be gated by the Walk motion controller",
    )
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
        "Component_Tamework_Instruction_Follow_Flying",
        "Component_Tamework_Instruction_Hold_Flying",
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


def check_species(names: tuple[str, ...]) -> None:
    for name in names:
        # Vanilla's source tuple stores the numeric fields as (WanderRadius, MaxHealth).
        directory, drop, radius, health, memories_override, favorite, particles, generic = SPECIES[name]
        wild_path = ROOT / "Server/NPC/Roles" / directory / f"{name}.json"
        tamed_path = ROOT / "Server/NPC/Roles" / directory / "Tamed" / f"Tamed_{name}.json"
        require(wild_path.exists(), f"missing {wild_path.relative_to(ROOT)}")
        require(tamed_path.exists(), f"missing {tamed_path.relative_to(ROOT)}")

        wild = load(wild_path)
        wild_modify = wild.get("Modify", {})
        require(wild.get("Type") == "Variant", f"{name} wild role must be a Variant")
        require(wild.get("Reference") == "AH_Template_Aerial_Neutral", f"{name} wild role uses wrong template")
        require(wild_modify.get("Appearance") == name, f"{name} wild appearance mismatch")
        require(wild_modify.get("FlockArray") == [name], f"{name} wild flock mismatch")
        require(wild_modify.get("DropList") == drop, f"{name} wild drop mismatch")
        require(wild_modify.get("MaxHealth") == health, f"{name} wild health mismatch")
        require(wild_modify.get("WanderRadius") == radius, f"{name} wild radius mismatch")
        if name == "Pterodactyl":
            require(wild_modify.get("GroundSpeed") == 4, "Pterodactyl wild GroundSpeed override must be 4")
        require(wild_modify.get("IsMemory") is True, f"{name} wild role must be a memory")
        require(wild_modify.get("MemoriesCategory") == "Avian", f"{name} wild memory category mismatch")
        if name == "Bluebird":
            require(wild_modify.get("MaxSpeed") == 20, "Bluebird wild MaxSpeed override must remain 20")
            require(wild_modify.get("ParticleOffset") == [0, 0.4, 0], "Bluebird wild ParticleOffset override must remain [0, 0.4, 0]")
        if memories_override is None:
            require("MemoriesNameOverride" not in wild_modify, f"{name} wild role has an unexpected memory name override")
        else:
            require(wild_modify.get("MemoriesNameOverride") == memories_override, f"{name} wild memory name override mismatch")
        require(wild_modify.get("NameTranslationKey") == {"Compute": "NameTranslationKey"}, f"{name} wild name key must be computed")
        require(wild_modify.get("AttractiveItemSet") == [favorite], f"{name} wild favorite item mismatch")
        require(wild_modify.get("AttractiveItemSetParticles") == particles, f"{name} wild food particle mismatch")
        require(wild_modify.get("IsTameable") == {"Compute": "IsTameable"}, f"{name} wild tameability must be computed")
        require(wild_modify.get("TameRoleChange") == {"Compute": "TameRoleChange"}, f"{name} wild role change must be computed")
        wild_parameters = wild.get("Parameters", {})
        require(
            wild_parameters.get("NameTranslationKey") == {
                "Value": f"server.npcRoles.{name}.name",
                "Description": "Translation key for NPC name display",
            },
            f"{name} wild translation key mismatch",
        )
        require(
            wild_parameters.get("IsTameable") == {
                "Value": True,
                "Description": "Whether this NPC can be tamed.",
            },
            f"{name} wild tameability parameter mismatch",
        )
        require(
            wild_parameters.get("TameRoleChange") == {
                "Value": f"Tamed_{name}",
                "Description": "The role the NPC will change into when it's tamed.",
            },
            f"{name} wild role-change parameter mismatch",
        )

        tamed = load(tamed_path)
        tamed_modify = tamed.get("Modify", {})
        require(tamed.get("Type") == "Variant", f"Tamed_{name} role must be a Variant")
        require(tamed.get("Reference") == "AH_Template_Aerial_Tamed", f"Tamed_{name} uses wrong template")
        require(tamed_modify.get("Appearance") == name, f"Tamed_{name} appearance mismatch")
        require(tamed_modify.get("FlockArray") == [f"Tamed_{name}"], f"Tamed_{name} flock mismatch")
        require(tamed_modify.get("DropList") == drop, f"Tamed_{name} drop mismatch")
        require(tamed_modify.get("MaxHealth") == health, f"Tamed_{name} health mismatch")
        require(tamed_modify.get("WanderRadius") == radius, f"Tamed_{name} radius mismatch")
        if name == "Pterodactyl":
            require(tamed_modify.get("GroundSpeed") == 4, "Tamed_Pterodactyl GroundSpeed override must be 4")
        require(tamed_modify.get("IsMemory") is False, f"Tamed_{name} role must not be a memory")
        require(tamed_modify.get("MemoriesCategory") == "Avian", f"Tamed_{name} memory category mismatch")
        if name == "Bluebird":
            require("MaxSpeed" not in tamed_modify, "Tamed_Bluebird must inherit the shared aerial flight-speed cap")
            require(tamed_modify.get("ParticleOffset") == [0, 0.4, 0], "Tamed_Bluebird ParticleOffset override must remain [0, 0.4, 0]")
            require(tamed_modify.get("NeedsSeekConsumeStartDistance") == 1.5, "Tamed_Bluebird NeedsSeekConsumeStartDistance override must remain 1.5")
            require(tamed_modify.get("NeedsSeekConsumeMaintainMaxDistance") == 1.25, "Tamed_Bluebird NeedsSeekConsumeMaintainMaxDistance override must remain 1.25")
            require(tamed_modify.get("NeedsSeekConsumeMaintainDistanceRange") == [1, 1.25], "Tamed_Bluebird NeedsSeekConsumeMaintainDistanceRange override must remain [1, 1.25]")
            require(tamed_modify.get("MemoriesNameOverride") == "Bluebird", "Tamed_Bluebird MemoriesNameOverride must remain Bluebird")
        require(tamed_modify.get("NameTranslationKey") == {"Compute": "NameTranslationKey"}, f"Tamed_{name} name key must be computed")
        require(tamed_modify.get("AttractiveItemSet") == [favorite], f"Tamed_{name} favorite item mismatch")
        require(tamed_modify.get("AttractiveItemSetParticles") == particles, f"Tamed_{name} food particle mismatch")
        require(tamed_modify.get("FoodFavorite") == [favorite], f"Tamed_{name} food favorite mismatch")
        require(tamed_modify.get("FoodGeneric") == list(generic), f"Tamed_{name} generic food mismatch")
        require(tamed_modify.get("AttitudeGroup") == "AH_Livestock_Tamed", f"Tamed_{name} attitude group mismatch")
        for flag in ("CanFollow", "CanHold", "CanMoveToLocation", "CanReturnHome", "CanRecall", "CanSetHome", "CanBreedPair"):
            require(tamed_modify.get(flag) is True, f"Tamed_{name} must enable {flag}")
        for flag in ("CanDefend", "CanAttackTarget"):
            require(tamed_modify.get(flag) is False, f"Tamed_{name} must disable {flag}")
        require(
            tamed.get("Parameters", {}).get("NameTranslationKey") == {
                "Value": f"server.npcRoles.{name}.name",
                "Description": "Translation key for NPC name display",
            },
            f"Tamed_{name} translation key mismatch",
        )


def check_configs() -> None:
    require(not LOCAL_FLYING_FOLLOW_COMPONENT.exists(), "local flying follow base must move to Tamework")
    require(not LOCAL_LARGE_FOLLOW_COMPONENT.exists(), "local large follow base must move to Tamework")
    require(
        not LOCAL_FROST_MODE_COMPONENT.exists(),
        "local Frost Dragon airborne-mode transition must move to Tamework",
    )
    require(
        load(ROOT / "manifest.json").get("Dependencies", {}).get("Alechilles:Alec's Tamework!")
        == ">=3.0 <4.0",
        "Animal Husbandry must require the Tamework release that publishes shared follow components",
    )
    frost_template = load(FROST_DRAGON_TEMPLATE)
    frost_mode = reference_nodes(
        frost_template, "Component_Tamework_Instruction_Airborne_Mode_Transition"
    )
    require(len(frost_mode) == 1, "Frost Dragon must consume shared airborne transition exactly once")
    require(
        frost_mode[0].get("Modify") == {
            "ToggleAirborneModeHookId": "AnimalHusbandry.Command.ToggleFrostDragonAirborneMode",
            "AirborneModeFlagName": "AirborneMode",
            "GroundedActivityFlagName": "AH_Dragon_Frost_UnusedGroundedActivity",
            "LandingRayName": "LandingRay",
            "LandingBlocks": "StoneAndSoil",
            "LandingSearchRange": 64,
            "LandingSearchAngle": 90,
            "LandingSlowDownDistance": 5,
            "LandingStopDistance": 0.5,
            "LandingHeightDifference": [-3, 2],
            "LandingGoalLenience": 3,
            "LandingDesiredAltitudeWeight": 0,
        },
        "Frost Dragon airborne transition tuning must remain explicit",
    )
    frost_ground = reference_nodes(frost_template, "Component_Tamework_Instruction_Follow_Large")
    require(len(frost_ground) == 1, "Frost Dragon must consume shared large follow exactly once")
    require(
        frost_ground[0].get("Modify") == {
            "MasterTargetSlot": "MasterTarget",
            "FollowTeleportThresholdRange": 60,
            "FollowSeekSlowDownDistance": 32,
            "FollowSeekStopDistance": 16,
            "FollowMaintainDistanceRange": [16, 24],
            "FollowRelativeSpeed": 1,
        },
        "Frost Dragon ground follow tuning must remain explicit",
    )
    frost_flying = reference_nodes(
        load(FROST_FLYING_FOLLOW_COMPONENT), "Component_Tamework_Instruction_Follow_Flying"
    )
    require(len(frost_flying) == 1, "Frost Dragon wrapper must consume shared flying follow exactly once")
    require(
        frost_flying[0].get("Modify") == {
            "MasterTargetSlot": "MasterTarget",
            "FollowDesiredAltitudeRange": [4, 8],
            "FollowTeleportThresholdRange": 60,
            "FollowOrbitRadiusRange": [16, 24],
            "FollowOrbitRetargetTimeRange": [3, 6],
            "FollowOrbitStopDistance": 3,
            "FollowOrbitRelativeSpeed": 0.65,
            "FollowHoverRadius": 1.75,
            "FollowHoverRelativeSpeed": 0.12,
        },
        "Frost Dragon flying follow and safe teleport tuning must remain explicit",
    )
    aerial = load(ROOT / "Server/Tamework/Companion/AHCompAerial.json")
    require(aerial.get("Parent") == "TwCompanionConfig_Default", "wrong aerial companion parent")
    require(aerial.get("Enabled") is True, "aerial companion must be enabled")
    require(aerial.get("Priority") == 10, "wrong aerial companion priority")
    aerial_role_ids = aerial.get("RoleIds")
    require(isinstance(aerial_role_ids, list), "aerial companion RoleIds must be a list")
    require(all(isinstance(item, str) for item in aerial_role_ids), "aerial companion RoleIds must contain strings")
    require(len(aerial_role_ids) == len(TAMED_IDS), "flight toggle role count drift")
    require(len(aerial_role_ids) == len(set(aerial_role_ids)), "flight toggle RoleIds contain duplicates")
    require(aerial_role_ids == list(TAMED_IDS), "flight toggle role order drift")
    require(
        aerial["Command"]["FlightToggle"] == {"Enabled": True, "HookId": HOOK_ID},
        "flight toggle contract drift",
    )
    frost_particles = FROST_DRAGON_TEMPLATE.exists() and load(FROST_DRAGON_TEMPLATE).get("Parameters", {}).get("AttractiveItemSetParticles")
    require(
        frost_particles == {
            "Value": "Want_Food_Wildmeat_Raw",
            "Description": "The particle system that spawns to indicate the NPC's liked item(s).",
        },
        "Frost Dragon template must expose AttractiveItemSetParticles for AHIntBeast",
    )
    require(
        load(FROST_DRAGON_ROLE).get("Modify", {}).get("AttractiveItemSetParticles")
        == "AH_Dragon_Frost_Want_Food_Ice_Essence",
        "Frost Dragon must retain its ice-essence food particle override",
    )
    tamed_ids = set(TAMED_IDS)
    wild_and_tamed = set(SPECIES) | tamed_ids
    for relative in (
        "Server/Tamework/Companion/AHCompNeutral.json",
        "Server/Tamework/CompanionMovement/AHCompanionMovement.json",
        "Server/Tamework/Happiness/AHHappNeutral.json",
        "Server/Tamework/Needs/AHNeedsMain.json",
        "Server/Tamework/Leveling/AHLevelNeutral.json",
        "Server/Tamework/Talents/AHTalentNeutral.json",
    ):
        check_membership(relative, ("RoleIds",), tamed_ids, tamed_ids, relative)
    for relative in (
        "Server/Tamework/Interactions/AHIntNeutral.json",
        "Server/Tamework/Breeding/AHBreedNeutral.json",
        "Server/Tamework/Traits/AHTraitNeutral.json",
    ):
        check_membership(relative, ("RoleIds",), wild_and_tamed, wild_and_tamed, relative)
        check_non_role_content(relative)
    interactions = load(INTERACTION_CONFIG).get("Interactions", [])
    wrong_food_cues = [
        interaction
        for interaction in interactions
        if interaction.get("Type") == "Custom"
        and interaction.get("Requires", {}).get("All", {}).get("IsNotTamed") is True
        and any(
            condition.get("ItemsParam") == "AttractiveItemSet" and condition.get("Operator") == "NoneOf"
            for condition in interaction.get("Requires", {}).get("All", {}).get("ItemsInHand", [])
        )
        and interaction.get("Effects", {}).get("SpawnParticles", {}).get("ParticleSystemParam")
        == "AttractiveItemSetParticles"
    ]
    require(len(wrong_food_cues) == 1, "neutral interaction config missing wrong-food thought bubble")
    check_membership(
        "Server/Tamework/Needs/AHNeedsOmnivore.json",
        ("RoleIds",),
        tamed_ids,
        OMNIVORE_IDS,
        "omnivore needs",
    )
    check_membership(
        "Server/Tamework/Needs/AHNeedsCarnivore.json",
        ("RoleIds",),
        tamed_ids,
        CARNIVORE_IDS,
        "carnivore needs",
    )
    group_ids = {f"{role_id}*" for role_id in TAMED_IDS}
    check_membership(
        "Server/NPC/Groups/AH_Livestock_Tamed.json",
        ("IncludeRoles",),
        group_ids,
        group_ids,
        "livestock group",
    )
    check_membership(
        "Server/Tamework/Items/Commands/AHCommLivestock.json",
        ("AllowedRoles", "Allowlist"),
        tamed_ids,
        tamed_ids,
        "livestock command",
    )
    check_membership(
        "Server/Tamework/Items/Spawners/AHSpawnSoulLantern.json",
        ("AllowedRoles", "Allowlist"),
        wild_and_tamed,
        wild_and_tamed,
        "Soul Lantern",
    )
    food_path = "Server/Tamework/Food/AHFoodNeutral.json"
    food_overrides = load(ROOT / food_path)["RoleOverrides"]
    baseline_food = baseline_load(food_path)["RoleOverrides"]
    food_feature_keys = set(SPECIES) | tamed_ids
    require(set(food_overrides) & food_feature_keys == food_feature_keys, "food feature key set drift")
    current_unrelated = {key: value for key, value in food_overrides.items() if key not in food_feature_keys}
    baseline_unrelated = {key: value for key, value in baseline_food.items() if key not in food_feature_keys}
    require(
        len(current_unrelated) == len(baseline_unrelated)
        and canonical_sha(current_unrelated) == canonical_sha(baseline_unrelated),
        "food unrelated RoleOverrides baseline drift",
    )
    for name, (_, _, _, _, _, favorite, _, generic) in SPECIES.items():
        wild_foods = food_overrides[name].get("Foods")
        tamed_foods = food_overrides[f"Tamed_{name}"].get("Foods")
        require(wild_foods == {"Preferred": [favorite]}, f"wild food payload drift for {name}")
        require(
            tamed_foods == {"Preferred": [favorite], "Compatible": list(generic)},
            f"tamed food payload drift for Tamed_{name}",
        )


AERIAL_SPECIES = (
    "Bluebird",
    "Sparrow",
    "Parrot",
    "Raven",
    "Crow",
    "Finch_Green",
    "Woodpecker",
    "Owl_Brown",
    "Owl_Snow",
    "Bat",
    "Bat_Ice",
)


def check_all() -> None:
    check_wild_shared()
    check_tamed_shared()
    check_species(tuple(SPECIES))
    check_configs()


SCOPES = {
    "wild-shared": check_wild_shared,
    "tamed-shared": check_tamed_shared,
    "aerial-species": lambda: check_species(AERIAL_SPECIES),
    "fowl-raptor-species": lambda: check_species(("Pigeon", "Duck", "Archaeopteryx", "Hawk", "Pterodactyl", "Vulture")),
    "configs": check_configs,
    "all": check_all,
}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--scope", choices=sorted(SCOPES), required=True)
    args = parser.parse_args()
    SCOPES[args.scope]()
