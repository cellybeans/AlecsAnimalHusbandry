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


SCOPES = {"wild-shared": check_wild_shared}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--scope", choices=sorted(SCOPES), required=True)
    args = parser.parse_args()
    SCOPES[args.scope]()
