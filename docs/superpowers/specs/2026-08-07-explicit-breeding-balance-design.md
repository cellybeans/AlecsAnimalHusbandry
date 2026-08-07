# Explicit Breeding Cooldowns and Growth Times

## Goal

Give every breeding-eligible Animal Husbandry species an explicit breeding
cooldown and time to reach adulthood. Values should reflect reproductive pace
while preventing renewable resources, valuable drops, rare creatures, mounts,
and powerful companions from scaling too cheaply.

## Scope

- Keep the 29 explicit profiles in `AHBreedBeast.json` unchanged.
- Complete 20 tamed-adult profiles in `AHBreedLivestock.json`.
- Complete 45 tamed-adult profiles in `AHBreedNeutral.json`.
- End with 94 tamed-adult profiles that explicitly resolve both values.
- Preserve existing gender-paired lifecycle families for deer and moose and
  baby-role families for livestock.
- Do not add cooldown overrides to wild or juvenile roles. The configs require
  a tamed adult, so those roles are resolver and lifecycle inputs rather than
  breeding-eligible profiles.

## Chosen Approach

Add per-role overrides to the existing breeding assets. Similar variants may
share values, but each eligible role will contain its own explicit fields. This
keeps tuning discoverable and avoids a new generator, schema, or shared balance
table.

Each role's `Cooldowns` object will contain:

- `BaseCooldownMinutes`: the value in the matrices below.
- `MinDelaySeconds`: 5% of the base cooldown, expressed as `base * 3`.
- `MaxDelaySeconds`: 15% of the base cooldown, expressed as `base * 9`.

This matches the proportional delay pattern already used by the beast profiles.
Growth remains world-time-scaled through the existing config timing basis.

## Balance Model

Real-world reproductive pace establishes the ordering among comparable
animals. Gameplay value then raises cooldown and growth values for renewable
production, valuable essence/chitin/hide, mount or flight utility, combat
strength, rarity, and fictional or elemental status.

The new profiles remain within the established beast scale:

- New cooldowns: 35–120 minutes.
- New growth times: 40–220 minutes.
- Existing beast cooldowns: 45–180 minutes.
- Existing beast growth times: 50–300 minutes.

## Livestock Matrix

| Tamed adult role | Cooldown (min) | Growth (min) | Balance basis |
| --- | ---: | ---: | --- |
| `Tamed_Bison` | 90 | 150 | Large mount and medium hide |
| `Tamed_Boar` | 60 | 90 | Common meat animal |
| `Tamed_Bunny` | 35 | 50 | Rapid small mammal |
| `Tamed_Camel` | 85 | 135 | Large mount |
| `Tamed_Chicken` | 60 | 60 | Rapid bird, slowed for renewable eggs |
| `Tamed_Chicken_Desert` | 60 | 60 | Chicken variant with renewable eggs |
| `Tamed_Cow` | 100 | 120 | Renewable milk and useful hide/meat |
| `Tamed_Goat` | 80 | 90 | Productive livestock |
| `Tamed_Horse` | 90 | 150 | High-utility mount |
| `Tamed_Mosshorn` | 110 | 180 | Large fantasy mount and special produce |
| `Tamed_Mosshorn_Plain` | 110 | 180 | Large fantasy mount and special produce |
| `Tamed_Mouflon` | 70 | 90 | Medium livestock |
| `Tamed_Pig` | 60 | 90 | Fast-reproducing meat animal |
| `Tamed_Pig_Wild` | 65 | 90 | Hardier pig variant |
| `Tamed_Rabbit` | 35 | 50 | Rapid small mammal |
| `Tamed_Ram` | 70 | 90 | Medium livestock |
| `Tamed_Sheep` | 90 | 100 | Renewable wool |
| `Tamed_Skrill` | 65 | 75 | Egg-producing fantasy fowl |
| `Tamed_Turkey` | 60 | 80 | Egg-producing fowl |
| `Tamed_Warthog` | 65 | 90 | Hardier meat animal |

## Neutral, Critter, and Aerial Matrix

| Tamed adult role | Cooldown (min) | Growth (min) | Balance basis |
| --- | ---: | ---: | --- |
| `Tamed_Antelope` | 75 | 110 | Medium mount and hide |
| `Tamed_Armadillo` | 60 | 80 | Sturdy chitin |
| `Tamed_Crab` | 75 | 90 | Aquatic mount |
| `Tamed_Deer_Doe` | 80 | 120 | Medium mount and hide |
| `Tamed_Deer_Stag` | 80 | 120 | Medium mount and hide |
| `Tamed_Bluebird` | 40 | 45 | Small common bird |
| `Tamed_Flamingo` | 55 | 75 | Medium bird |
| `Tamed_Hatworm` | 40 | 45 | Small critter |
| `Tamed_Horse_Skeleton` | 110 | 180 | Rare undead mount |
| `Tamed_Horse_Skeleton_Armored` | 120 | 210 | Rare armored undead mount |
| `Tamed_Lizard_Sand` | 60 | 80 | Medium hide-bearing reptile |
| `Tamed_Lobster` | 80 | 100 | Aquatic mount |
| `Tamed_Moose_Bull` | 100 | 180 | Very large mount and hide |
| `Tamed_Moose_Cow` | 100 | 180 | Very large mount and hide |
| `Tamed_Penguin` | 55 | 75 | Medium bird |
| `Tamed_Spark_Living` | 120 | 220 | Elemental creature with fire essence |
| `Tamed_Tetrabird` | 90 | 150 | Large mount and feathers |
| `Tamed_Tortoise` | 90 | 160 | Slow-maturing mount with sturdy chitin |
| `Tamed_Trillodon` | 110 | 200 | Rare fantasy mount with heavy hide |
| `Tamed_Cactee` | 90 | 150 | Fictional combat-capable creature |
| `Tamed_Frog_Blue` | 40 | 45 | Rapid small amphibian |
| `Tamed_Frog_Green` | 40 | 45 | Rapid small amphibian |
| `Tamed_Frog_Orange` | 45 | 50 | Hardier amphibian variant |
| `Tamed_Gecko` | 40 | 45 | Rapid small reptile |
| `Tamed_Meerkat` | 45 | 55 | Small mammal |
| `Tamed_Mouse` | 35 | 40 | Fastest small mammal |
| `Tamed_Squirrel` | 40 | 50 | Rapid small mammal |
| `Tamed_Snail_Frost` | 90 | 140 | Renewable ice essence pressure |
| `Tamed_Snail_Magma` | 95 | 150 | Renewable fire essence pressure |
| `Tamed_Sparrow` | 35 | 40 | Fast common bird |
| `Tamed_Parrot` | 50 | 65 | Longer-lived companion bird |
| `Tamed_Raven` | 50 | 65 | Intelligent companion bird |
| `Tamed_Crow` | 45 | 60 | Common intelligent bird |
| `Tamed_Finch_Green` | 35 | 40 | Fast common bird |
| `Tamed_Woodpecker` | 45 | 55 | Small bird |
| `Tamed_Owl_Brown` | 60 | 80 | Raptor companion |
| `Tamed_Owl_Snow` | 60 | 80 | Raptor companion |
| `Tamed_Bat` | 45 | 55 | Rapid small flying mammal |
| `Tamed_Bat_Ice` | 60 | 80 | Elemental bat variant |
| `Tamed_Pigeon` | 40 | 45 | Fast common bird |
| `Tamed_Duck` | 50 | 60 | Common waterfowl |
| `Tamed_Archaeopteryx` | 90 | 140 | Rare flying-beast utility |
| `Tamed_Hawk` | 60 | 85 | Raptor companion |
| `Tamed_Pterodactyl` | 110 | 200 | Large rare flying creature |
| `Tamed_Vulture` | 65 | 90 | Large raptor companion |

## Validation

No new source-shape test will be added. Validation will use production-facing
asset workflows:

1. Parse all modified JSON assets.
2. Check the exact `release-0.5.7` project profile.
3. Run affected-scope Hytale asset validation for both breeding configs.
4. Resolve every eligible tamed-adult role and confirm it receives positive
   cooldown and growth values with a valid delay range.
5. Review the final diff for preserved family, pairing, gender, inheritance,
   and species-specific overrides.

## Evidence and Constraints

The design uses the existing beast profiles as calibration anchors: rat at
45/50, fox at 60/90, hyena at 75/120, crocodile at 100/200, yeti at 120/220,
and Frost Dragon at 180/300. Hytale Workshop release 0.5.7 gamedata confirms
the important value outliers, including chicken eggs, cow milk, sheep wool,
frost/magma snail and Spark Living essences, sturdy chitin from tortoise and
armadillo, heavy hide from Trillodon, and feather-bearing aerial species.
