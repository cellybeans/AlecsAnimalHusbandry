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
