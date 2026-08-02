# Frost Dragon Feeding and Breath Design

## Goal

Make Frost Essence the Frost Dragon's Animal Husbandry taming and preferred-feeding item, retain Carnivore Kibble as a lower-happiness alternative, and replace the current misplaced puff effects with a mouth-anchored frost stream and dedicated breath audio.

## Confirmed context

- The wild Frost Dragon uses `AHIntBeast`. Its tame entry accepts `AttractiveItemSet` only while the dragon is tranquilized and at or below 20% health, then changes it to `Tamed_Dragon_Frost`.
- The tamed Frost Dragon also uses `AHIntBeast`. Its feed entry accepts both `AttractiveItemSet` and `Tw_Feed_Carnivore`.
- `AHFoodBeast` currently gives preferred food `+5` happiness and compatible food `-8` happiness. Carnivore Kibble is already the compatible beast food.
- Hytale release 0.5.7 identifies Frost Essence as `Ingredient_Ice_Essence`.
- The Frost Dragon's standard and AvatarFlight models both contain a `Top Jaw` node. The AvatarFlight model renames only the parent head node to `AF_Head`.
- Current breath interactions attach the short `Ice_Staff` particle system to `Head` with a negative Z offset. Frost Bolt charging uses the same backwards head-relative pattern, and projectile launch uses an entity-relative offset of Y `2.25`, Z `-2.5`.

## Feeding and taming

The wild role will explicitly set `AttractiveItemSet` to `Ingredient_Ice_Essence`. This preserves the existing Animal Husbandry admission flow: the player must weaken and tranquilize the dragon before feeding the essence. The tame prompt and action both receive the same role parameter, so no new interaction config is required.

The tamed role will set `AttractiveItemSet` to `Ingredient_Ice_Essence`. Its `AHFoodBeast` role override will list Frost Essence as `Preferred`. The family-level `Compatible` list will continue to contain `Tw_Feed_Carnivore`, so both items remain feedable while resolving to these happiness outcomes:

| Item | Category | Happiness |
| --- | --- | ---: |
| Frost Essence (`Ingredient_Ice_Essence`) | Preferred | +5 |
| Carnivore Kibble (`Tw_Feed_Carnivore`) | Compatible | -8 |

Raw wildmeat will no longer be accepted as the Frost Dragon's preferred or taming item.

## Breath particles

Add one mod-owned particle system composed of narrow, continuously emitting ice-mist and crystal spawners. It will follow the vanilla flamethrower stream pattern—continuous spawn rate, forward velocity, short particle lifespan, and a narrow cone—but use ice/snow textures and pale blue-white colors.

All ground, aerial, and AvatarFlight breath interactions will:

- target `Top Jaw`;
- use the new Frost Dragon stream system;
- keep `DetachedFromModel` false so the emission origin follows the animated, moving mouth;
- use a small positive local-Z offset and the existing 180-degree particle rotation needed by forward-stream particle orientation;
- retain the current 1.2-second animation and four-hit damage cadence.

No permanent model particle will be added because the breath must exist only while attacking.

## Breath audio

Add Frost Dragon-specific start/loop and end SoundEvent assets plus a short source EntityEffect following the vanilla `FlamethrowerSource` lifecycle:

- the start event layers an ice-cast transient with a sustained mono wind layer;
- the source effect has a 0.5-second duration and overwrite behavior;
- breath interactions refresh the source effect during their existing damage cadence;
- when refreshing stops, effect removal stops the loop and plays a short ice-break end event.

The SoundEvents will reference shipped Hytale audio paths rather than redistribute base-game audio files. Ground, aerial, and mounted breath share this one Frost Dragon sound family.

## Mouth-origin correction

Frost Bolt charge particles will target `Top Jaw` in both NPC and AvatarFlight interactions. Their positive local-Z offsets will place the charge at the mouth instead of behind the head.

`TameworkLaunchProjectile` currently supports only an entity-relative launch offset, not a model-node launch anchor. The two Frost Bolt interactions will therefore use a corrected entity-relative mouth approximation with lower Y and positive Z. This is sufficient for an instantaneous projectile launch and avoids a cross-repository Tamework Java/API change.

## Scope and non-goals

- Keep Frost Bolt and breath damage, cooldowns, targeting, and status effects unchanged.
- Keep the Frost Dragon's existing tame health/tranquilizer requirements unchanged.
- Do not alter Nordic Drake assets.
- Do not modify Frost Dragon models or animations.
- Do not change generic beast feeding behavior for other species.

## Verification

Add one focused contract check that loads the real role, food, interaction, particle, sound, and effect assets and verifies:

- wild taming and tamed preferred feeding resolve to Frost Essence;
- Carnivore Kibble remains compatible at `-8` happiness;
- raw wildmeat is absent from Frost Dragon overrides;
- every breath variant uses the attached `Top Jaw` stream and refreshes the dedicated source effect;
- both Frost Bolt variants charge at `Top Jaw` and launch with the corrected mouth offset;
- every referenced new particle spawner, SoundEvent, and EntityEffect exists.

Run the focused check red before implementation and green afterward. Then parse all changed JSON, run the existing Frost Dragon combat checks, perform exact-profile affected-scope asset validation, and inspect the final diff. Live visual/audio verification remains an explicit in-game follow-up because static validation cannot prove final mouth alignment, stream density, or perceived mix level.
