# Vanilla Passive Flying Companions Design

## Goal

Add Animal Husbandry taming and full non-combat companion support to every vanilla role that inherits Hytale 0.5.7's `Template_Birds_Passive`, while preserving each wild animal's vanilla flight, flocking, panic, and flee behavior whenever no player is holding its favorite food.

## Scope

The inclusion rule is role inheritance, not folder or group membership. The targeted wild roles are:

- `Bluebird`
- `Sparrow`
- `Parrot`
- `Raven`
- `Crow`
- `Finch_Green`
- `Woodpecker`
- `Owl_Brown`
- `Owl_Snow`
- `Bat`
- `Bat_Ice`
- `Pigeon`
- `Duck`
- `Archaeopteryx`
- `Hawk`
- `Pterodactyl`
- `Vulture`

Each wild role receives a corresponding `Tamed_<RoleId>` role.

Flamingo, Penguin, Tetrabird, Chicken, and Turkey are excluded because their effective vanilla roles use grounded neutral or livestock templates rather than `Template_Birds_Passive`. Temple/test bird roles are also excluded. Combat behavior, mounts, attacks, defend mode, and attack-target mode are out of scope.

Existing unrelated Frost Dragon, Tetrabird, Avatar Flight, and Tamework working-tree changes are not part of this feature and must not be reverted or folded into its commits.

## Evidence and Compatibility Contract

The base-game contract is grounded in the Hytale Workshop 0.5.7 release corpus:

- `Server/NPC/Roles/_Core/Templates/Template_Birds_Passive.json` supplies the vanilla Fly controller, altitude range, flocking, idle flight, panic, and flee behavior.
- `EntityFilterItemInHand` at `com.hypixel.hytale.server.npc.corecomponents.entity.filters.EntityFilterItemInHand` stops matching as soon as the player puts the item away.
- `BodyMotionTakeOff` and `BodyMotionLand` are the supported Walk/Fly controller transitions.
- `Server/NPC/Roles/_Core/Tests/Birds/Test_Bird_Seek.json`, `Test_Bird_Land.json`, and `Test_Bird_TakeOff.json` demonstrate the relevant flight seek, landing, and takeoff semantics.

Animal Husbandry remains a required downstream consumer of Alec's Tamework 3.x. The implementation consumes the current Tamework `FlightToggle` companion config, `TameworkHook`, `TameworkSetFlyingCompanionMode`, and flying-companion landing controller. The working Tamework checkout is based on commit `6e6a28703` and currently contains the flight-toggle UI/service work as uncommitted source. This Animal Husbandry feature must not be published before that Tamework feature is committed and included in the matching Tamework release. No Tamework Java changes are required by this design.

The Animal Husbandry manifest retains its required dependency range `Alechilles:Alec's Tamework! >=3.0 <4.0`, which includes the current 3.0.0 development baseline.

## Architecture

The feature uses two shared templates and thin per-species variants:

1. `AH_Template_Aerial_Neutral` preserves the effective vanilla passive-bird behavior and adds favorite-item attraction, safe landing, grounded approach, feeding, and tame-role transition.
2. `AH_Template_Aerial_Tamed` supplies the complete Animal Husbandry lifecycle plus land/flight branches for non-combat companion commands.
3. A reusable Animal Husbandry airborne-mode transition component consumes the stable hook `AnimalHusbandry.Command.ToggleAirborneMode`, flips `AirborneMode`, and performs TakeOff or safe landing without changing the current command state.
4. A dedicated higher-priority `TwCompanionConfig` applies `Command.FlightToggle` only to the 17 tamed aerial roles. Grounded neutral animals must not inherit the flight toggle.
5. Wild and tamed role files contain only species data: appearance, drops, flock IDs, health, wander radius, name/memory values, food profile, and tame-role mapping.

This avoids per-species behavior copies and avoids patch-order dependence. Species-specific vanilla values remain unchanged unless this specification explicitly assigns a food or tame role.

## Favorite Foods

The compact food map uses verified Hytale 0.5.7 item IDs:

| Favorite | Roles | Desire particle |
| --- | --- | --- |
| `Plant_Crop_Corn_Item` | Bluebird, Sparrow, Finch_Green, Pigeon, Duck, Woodpecker, Crow, Raven | `Want_Food_Corn` |
| `Plant_Fruit_Apple` | Parrot, Bat, Bat_Ice | `Want_Food_Apple` |
| `Food_Wildmeat_Raw` | Archaeopteryx, Hawk, Owl_Brown, Owl_Snow, Pterodactyl, Vulture | Omitted because Hytale 0.5.7 has no verified matching native desire particle |

Corn/apple roles use `Tw_Feed_Herbivore` as compatible feed. Crow, Raven, Duck, and Woodpecker additionally accept `Tw_Feed_Carnivore` as compatible feed. Raw-meat roles use `Tw_Feed_Carnivore`. The favorite item is used consistently by wild attraction, taming, hand feeding, autonomous food selection, and happiness impulses.

## Wild Behavior

Vanilla danger behavior has priority over food attraction. Panic, flee, damage response, flocking, and leash constraints remain effective even when a player holds food.

When no valid player holds the favorite item, the animal follows the unchanged vanilla aerial idle path.

When a player within the configured view range holds the favorite item:

1. The animal marks the player as `InteractionTarget` and enters its food-follow state.
2. While airborne and outside the landing approach radius, it flies toward the player using the Fly controller and a bounded seek speed.
3. Once close, it invokes Tamework's safe landing controller using `InteractionTarget` as the landing origin. The controller selects a safe stand position a few blocks around the player; exact player-facing placement is not required.
4. After touchdown, the animal uses the Walk controller to close the remaining distance and waits within normal feeding range.
5. A valid feed interaction consumes one favorite item, plays the normal taming feedback, changes the role to `Tamed_<RoleId>`, and initializes the companion in landed Idle mode.

If the held item disappears or the target leaves range while the animal is still freely flying, it immediately releases the target and returns to vanilla aerial idle. If the animal is already committed to a safe landing, it finishes touchdown, releases the target, takes off, and then returns to vanilla aerial idle. A failed or obstructed landing remains airborne and retries safely; it must not teleport through blocks or switch to Walk in midair.

## Tamed Locomotion and Commands

Newly tamed, loaded, recalled without a prior runtime mode, or respawned aerial companions initialize as:

- command state: `Idle`
- `AirborneMode`: false
- active controller: Walk

The Tamework command UI exposes one flight toggle for the dedicated aerial companion config. Dispatching `AnimalHusbandry.Command.ToggleAirborneMode` changes locomotion without changing the active command.

| Command | Land mode | Flight mode |
| --- | --- | --- |
| Idle | Ground wander | Small aerial wander |
| Follow | Tamework advanced grounded follow | Tamework flying follow and nearby hover |
| Hold | Remain still on the ground | Hover in place |
| Command Move / Return Home | Use grounded movement | Use the active flying controller where the command supports it |
| Recall | Place safely, then restore the selected mode | Place safely, then restore the selected mode |
| Set Home | Record the home location without changing mode | Record the home location without changing mode |

The selected mode persists while changing among Idle, Follow, and Hold. Switching to flight uses `BodyMotionTakeOff`. Switching to land uses Tamework's safe landing controller and then activates Walk. Hold in flight mode does not land. Defend, Attack Target, Aggressive, and all combat actions remain disabled.

## Full Husbandry Lifecycle

The tamed roles participate in the same non-combat Animal Husbandry systems as other neutral companions:

- ownership and owner-damage policy
- favorite and compatible food profiles
- hunger and thirst decay
- hand feeding and bucket watering
- autonomous eating from configured containers or troughs
- autonomous drinking from nearby water
- happiness equilibrium and hunger, thirst, social, owner, feeding, and petting modifiers
- passive and interaction-driven breeding
- gender, cooldowns, population limits, and pregnancy timing
- inherited ownership, tame state, attachments, and traits
- scaled offspring growth
- traits, talents, leveling, and companion movement modifiers
- Follow, Hold, Move to Location, Set Home, Return Home, Recall, and command-item integration
- Soul Lantern capture/restore with role and companion data preserved

Autonomous eating, drinking, sleeping, and breeding are grounded activities. A companion already in land mode walks to the resource or partner. A companion in flight mode temporarily performs a safe landing near the resource or partner, walks into interaction range, completes the activity, restores its prior command, and retakes flight because `AirborneMode` remains selected.

Breeding uses the existing neutral contract: both partners must be tamed adults, sufficiently happy, awake, out of combat, within the breed radius, under the nearby-population cap, and of compatible opposite genders. `RequireSameRoleId` remains true. Because the 17 species have no separate baby role assets, offspring use the same tamed role and the existing 0.8-scale-to-adult lifecycle over 90 minutes.

Configuration membership is explicit:

- Add all 17 tamed roles to `Server/Tamework/Companion/AHCompNeutral.json`, `Server/Tamework/CompanionMovement/AHCompanionMovement.json`, `Server/Tamework/Happiness/AHHappNeutral.json`, `Server/Tamework/Needs/AHNeedsMain.json`, `Server/Tamework/Interactions/AHIntNeutral.json`, `Server/Tamework/Leveling/AHLevelNeutral.json`, `Server/Tamework/Talents/AHTalentNeutral.json`, and `Server/Tamework/Traits/AHTraitNeutral.json`.
- Add all 17 wild/tamed pairs as role overrides in `Server/Tamework/Food/AHFoodNeutral.json` and as role IDs in `Server/Tamework/Breeding/AHBreedNeutral.json`, matching the existing Bluebird neutral-animal pattern.
- Add `Tamed_Crow`, `Tamed_Raven`, `Tamed_Duck`, and `Tamed_Woodpecker` to `Server/Tamework/Needs/AHNeedsOmnivore.json`.
- Add `Tamed_Archaeopteryx`, `Tamed_Hawk`, `Tamed_Owl_Brown`, `Tamed_Owl_Snow`, `Tamed_Pterodactyl`, and `Tamed_Vulture` to `Server/Tamework/Needs/AHNeedsCarnivore.json`.
- Add all 17 tamed roles to `Server/NPC/Groups/AH_Livestock_Tamed.json`, `Server/Tamework/Items/Commands/AHCommLivestock.json`, and `Server/Tamework/Items/Spawners/AHSpawnSoulLantern.json`.
- Keep ownership, command, needs, happiness, traits, talents, leveling, movement, group, and Soul Lantern membership tamed-only. Wild roles receive only the food and breeding-family registrations already used for pre-tame neutral animals.

## State Recovery and Failure Behavior

- Losing a favorite-item target releases `InteractionTarget` and restores vanilla idle behavior.
- Losing a food, water, sleep, breed, home, or owner target cancels that subtask and restores the previous valid command.
- Losing a landing target keeps the NPC on Fly and retries or safely falls back to a local stand search; it never activates Walk while unsupported.
- A blocked landing does not teleport the animal or force it through collision.
- Toggle requests are exposed only when `FlightToggle.Enabled` is true, the hook is nonblank, the player owns the NPC, the NPC is linked to the command item, and its active controller is Fly or Walk.
- Reloading or respawning without a persisted runtime flight selection returns the companion to landed Idle, as approved.
- Vanilla panic/flee can interrupt wild attraction. Tamed needs and husbandry subtasks do not enable combat or hostile target acquisition.

## Validation

The implementation is asset-only, so no Java unit tests are added. The approved verification contract is exact-profile candidate validation plus generated static behavior checks.

Use `C:\Users\22ale\AppData\Roaming\Hytale\Modding\Alec's Animal Husbandry!\.asset-tools\project-profile.json`, currently ready for Hytale release 0.5.7 with profile identity SHA-256 `73ebffbbc2eeb78b637582eb93553df322db865158718d6a8f6b3da0db3cf128`. The current profile has schema/plugin descriptors and source semantics but no authoring-knowledge pack. Refresh the asset snapshot after source materialization before final affected-scope validation.

Validation must include:

1. Declared and effective inspection for one small bird, one bat, one fowl, and one raptor/outlier.
2. Exact-profile builder/options confirmation for every newly consumed action, sensor, filter, component, hook, and config field.
3. A multi-file candidate covering all 17 wild roles, all 17 tamed roles, both shared templates, reusable components, and every role-scoped configuration update.
4. `author validate --scope affected` followed by materialized-source affected validation and generated static verification.
5. A consistency comparison proving every target has the correct template, tame-role reference, favorite food, feed family, non-combat command flags, and configuration membership.
6. Static scenarios for wild idle, held-food acquisition, flight approach, safe landing, grounded approach, item removal before and during landing, taming, landed/airborne Idle, Follow, Hold, mode toggling, Move/Return/Recall, autonomous food and water seeking, sleep, breeding, offspring growth, capture, and restore.
7. Explicit reporting of target-loss, landing, runtime animation, live pathfinding, and multiplayer behavior that static verification cannot prove. No live harness run is authorized by this design.

The source batch must stop rather than guess if any structural class lacks exact-profile support or if Tamework registration and the locked profile disagree.
