param(
    [string] $Root = (Get-Location).Path
)

$ErrorActionPreference = "Stop"
$failures = New-Object System.Collections.Generic.List[string]

function Add-Failure([string] $Message) {
    $failures.Add($Message)
}

function Get-PropertyValue($Object, [string] $Name) {
    if ($null -eq $Object) {
        return $null
    }

    $property = $Object.PSObject.Properties[$Name]
    if ($null -eq $property) {
        return $null
    }

    return $property.Value
}

function Read-JsonAsset([string] $RelativePath) {
    $path = Join-Path $Root $RelativePath
    if (-not (Test-Path -LiteralPath $path -PathType Leaf)) {
        Add-Failure "missing required asset: $RelativePath"
        return $null
    }

    try {
        return Get-Content -LiteralPath $path -Raw | ConvertFrom-Json
    } catch {
        Add-Failure "invalid JSON asset ${RelativePath}: $($_.Exception.Message)"
        return $null
    }
}

function Read-JsonCandidate([string] $Label, [string[]] $RelativePaths) {
    foreach ($relativePath in $RelativePaths) {
        $path = Join-Path $Root $relativePath
        if (Test-Path -LiteralPath $path -PathType Leaf) {
            return Read-JsonAsset $relativePath
        }
    }

    Add-Failure "missing required $Label (checked: $($RelativePaths -join ', '))"
    return $null
}

# Walk every object and array while retaining a useful JSON-like path.  The
# contract checks below deliberately use this instead of regexes so malformed
# or misplaced values are reported rather than silently skipped.
function Get-JsonPropertyEntries($Value, [string] $PropertyName, [string] $Path = "root") {
    $entries = @()
    if ($null -eq $Value) {
        return $entries
    }

    if ($Value -is [System.Collections.IEnumerable] -and $Value -isnot [string]) {
        $index = 0
        foreach ($item in $Value) {
            $entries += @(Get-JsonPropertyEntries $item $PropertyName "$Path[$index]")
            $index++
        }
        return $entries
    }

    if ($Value -is [pscustomobject]) {
        foreach ($property in @($Value.PSObject.Properties)) {
            $propertyPath = "$Path.$($property.Name)"
            if ($property.Name -eq $PropertyName) {
                $entries += [pscustomobject]@{
                    Path = $propertyPath
                    Value = $property.Value
                }
            }
            $entries += @(Get-JsonPropertyEntries $property.Value $PropertyName $propertyPath)
        }
    }

    return $entries
}

function Get-JsonScalarEntries($Value, [string] $Path = "root") {
    $entries = @()
    if ($null -eq $Value) {
        return $entries
    }

    if ($Value -is [System.Collections.IEnumerable] -and $Value -isnot [string]) {
        $index = 0
        foreach ($item in $Value) {
            $entries += @(Get-JsonScalarEntries $item "$Path[$index]")
            $index++
        }
        return $entries
    }

    if ($Value -is [pscustomobject]) {
        foreach ($property in @($Value.PSObject.Properties)) {
            $entries += @(Get-JsonScalarEntries $property.Value "$Path.$($property.Name)")
        }
        return $entries
    }

    $entries += [pscustomobject]@{
        Path = $Path
        Value = $Value
    }
    return $entries
}

function Get-JsonObjectEntries($Value, [string] $Path = "root") {
    $entries = @()
    if ($null -eq $Value) {
        return $entries
    }

    if ($Value -is [System.Collections.IEnumerable] -and $Value -isnot [string]) {
        $index = 0
        foreach ($item in $Value) {
            $entries += @(Get-JsonObjectEntries $item "$Path[$index]")
            $index++
        }
        return $entries
    }

    if ($Value -is [pscustomobject]) {
        $entries += [pscustomobject]@{
            Path = $Path
            Value = $Value
        }
        foreach ($property in @($Value.PSObject.Properties)) {
            $entries += @(Get-JsonObjectEntries $property.Value "$Path.$($property.Name)")
        }
    }

    return $entries
}

function Convert-ToNumber($Value) {
    if ($null -eq $Value) {
        return $null
    }

    try {
        return [double] $Value
    } catch {
        return $null
    }
}

function Test-PositiveRange($Value) {
    if ($null -eq $Value) {
        return $false
    }

    $min = Get-PropertyValue $Value "Min"
    $max = Get-PropertyValue $Value "Max"
    if ($null -ne $min -or $null -ne $max) {
        $minNumber = Convert-ToNumber $min
        $maxNumber = Convert-ToNumber $max
        return $null -ne $minNumber -and $null -ne $maxNumber -and $minNumber -gt 0 -and $maxNumber -gt 0
    }

    $number = Convert-ToNumber $Value
    return $null -ne $number -and $number -gt 0
}

function Assert-Contains([object] $Value, [string] $Expected, [string] $Path) {
    $actual = @()
    if ($null -ne $Value) {
        $actual = @($Value)
    }
    if ($actual -notcontains $Expected) {
        Add-Failure "$Path must contain '$Expected' (actual: $($actual -join ', '))"
    }
}

function Assert-ExactSingle([object] $Value, [string] $Expected, [string] $Path) {
    $actual = @()
    if ($null -ne $Value) {
        $actual = @($Value)
    }
    if ($actual.Count -ne 1 -or $actual[0] -ne $Expected) {
        Add-Failure "$Path must be ['$Expected'] (actual: $($actual -join ', '))"
    }
}

$wildRolePath = "Server/NPC/Roles/Boss/Dragon_Frost.json"
$tamedRolePath = "Server/NPC/Roles/Creature/Mythic/Tamed/Tamed_Dragon_Frost.json"
$foodPath = "Server/Tamework/Food/AHFoodBeast.json"
$foodThoughtSystemPath = "Server/Particles/AnimalHusbandry/Dragon_Frost/AH_Dragon_Frost_Want_Food_Ice_Essence.particlesystem"
$foodThoughtSpawnerPath = "Server/Particles/AnimalHusbandry/Dragon_Frost/Spawners/AH_Dragon_Frost_ThoughtCloud_Ice_Essence.particlespawner"
$foodThoughtTexturePath = "Common/Particles/AnimalHusbandry/Thoughts/IceEssenceThought.png"
$boltPaths = @(
    "Server/Item/Interactions/NPCs/AnimalHusbandry/Dragon_Frost/AH_Dragon_Frost_Frost_Bolt.json",
    "Server/Item/Interactions/NPCs/AnimalHusbandry/Dragon_Frost/AH_Dragon_Frost_Avatar_Frost_Bolt.json"
)
$breathPaths = @(
    "Server/Item/Interactions/NPCs/AnimalHusbandry/Dragon_Frost/AH_Dragon_Frost_Freezing_Breath.json",
    "Server/Item/Interactions/NPCs/AnimalHusbandry/Dragon_Frost/AH_Dragon_Frost_Flying_Freezing_Breath.json",
    "Server/Item/Interactions/NPCs/AnimalHusbandry/Dragon_Frost/AH_Dragon_Frost_Avatar_Freezing_Breath.json"
)
$particleSystemPath = "Server/Particles/AnimalHusbandry/Dragon_Frost/AH_Dragon_Frost_Freezing_Breath.particlesystem"
$spawnerPaths = @(
    "Server/Particles/AnimalHusbandry/Dragon_Frost/Spawners/AH_Dragon_Frost_Freezing_Breath_Mist.particlespawner",
    "Server/Particles/AnimalHusbandry/Dragon_Frost/Spawners/AH_Dragon_Frost_Freezing_Breath_Crystals.particlespawner"
)
$breathRoarSoundPath = "Server/Audio/SoundEvents/SFX/NPC/Mythic/Dragon_Frost/SFX_AH_Dragon_Frost_Breath_Roar.json"
$boltLaunchSoundPath = "Server/Audio/SoundEvents/SFX/NPC/Mythic/Dragon_Frost/SFX_AH_Dragon_Frost_Frost_Bolt_Launch.json"
$breathRoarAudioPath = "Common/Sounds/AnimalHusbandry/Dragon_Frost/Avatar_Flame_Breath_Roar.ogg"
$boltLaunchAudioPath = "Common/Sounds/AnimalHusbandry/Dragon_Frost/Avatar_Fireball_Launch.ogg"
$sourceEffectPath = "Server/Entity/Effects/Status/AnimalHusbandry/AH_Dragon_Frost_Freezing_Breath_Source.json"

$wildRole = Read-JsonAsset $wildRolePath
$tamedRole = Read-JsonAsset $tamedRolePath
$food = Read-JsonAsset $foodPath
$foodThoughtSystem = Read-JsonAsset $foodThoughtSystemPath
$foodThoughtSpawner = Read-JsonAsset $foodThoughtSpawnerPath
$boltInteractions = @{}
foreach ($path in $boltPaths) {
    $boltInteractions[$path] = Read-JsonAsset $path
}
$breathInteractions = @{}
foreach ($path in $breathPaths) {
    $breathInteractions[$path] = Read-JsonAsset $path
}
$particleSystem = Read-JsonAsset $particleSystemPath
$spawners = @{}
foreach ($path in $spawnerPaths) {
    $spawners[$path] = Read-JsonAsset $path
}
$breathRoarSound = Read-JsonAsset $breathRoarSoundPath
$boltLaunchSound = Read-JsonAsset $boltLaunchSoundPath
$sourceEffect = Read-JsonAsset $sourceEffectPath

foreach ($audioPath in @($breathRoarAudioPath, $boltLaunchAudioPath)) {
    if (-not (Test-Path -LiteralPath (Join-Path $Root $audioPath) -PathType Leaf)) {
        Add-Failure "missing required audio asset: $audioPath"
    }
}

if (-not (Test-Path -LiteralPath (Join-Path $Root $foodThoughtTexturePath) -PathType Leaf)) {
    Add-Failure "missing required food thought texture: $foodThoughtTexturePath"
}

$standardModel = Read-JsonCandidate "standard Frost Dragon model" @(
    "Server/Models/AnimalHusbandry/AH_Dragon_Frost.blockymodel",
    "Common/NPC/AnimalHusbandry/Dragon_Frost/Models/Model.blockymodel"
)
$avatarModel = Read-JsonCandidate "AvatarFlight Frost Dragon model" @(
    "Server/Models/AnimalHusbandry/AH_Dragon_Frost_AvatarFlight.blockymodel",
    "Common/NPC/AnimalHusbandry/Dragon_Frost/Models/Model_AvatarFlight.blockymodel"
)

if ($null -ne $wildRole) {
    Assert-ExactSingle (Get-PropertyValue $wildRole.Modify "AttractiveItemSet") "Ingredient_Ice_Essence" "$wildRolePath Modify.AttractiveItemSet"
    if ([string](Get-PropertyValue $wildRole.Modify "AttractiveItemSetParticles") -ne "AH_Dragon_Frost_Want_Food_Ice_Essence") {
        Add-Failure "$wildRolePath Modify.AttractiveItemSetParticles must be AH_Dragon_Frost_Want_Food_Ice_Essence"
    }
}
if ($null -ne $tamedRole) {
    Assert-ExactSingle (Get-PropertyValue $tamedRole.Modify "AttractiveItemSet") "Ingredient_Ice_Essence" "$tamedRolePath Modify.AttractiveItemSet"
    if ([string](Get-PropertyValue $tamedRole.Modify "AttractiveItemSetParticles") -ne "AH_Dragon_Frost_Want_Food_Ice_Essence") {
        Add-Failure "$tamedRolePath Modify.AttractiveItemSetParticles must be AH_Dragon_Frost_Want_Food_Ice_Essence"
    }
}
if ($null -ne $foodThoughtSystem) {
    Assert-Contains (Get-JsonPropertyEntries $foodThoughtSystem "SpawnerId" | ForEach-Object { $_.Value }) "AH_Dragon_Frost_ThoughtCloud_Ice_Essence" "$foodThoughtSystemPath Spawners"
}
if ($null -ne $foodThoughtSpawner) {
    if ([string](Get-PropertyValue (Get-PropertyValue $foodThoughtSpawner "Particle") "Texture") -ne "Particles/AnimalHusbandry/Thoughts/IceEssenceThought.png") {
        Add-Failure "$foodThoughtSpawnerPath Particle.Texture must be Particles/AnimalHusbandry/Thoughts/IceEssenceThought.png"
    }
}
if ($null -ne $food) {
    Assert-Contains (Get-PropertyValue $food.Foods "Compatible") "Tw_Feed_Carnivore" "$foodPath Foods.Compatible"

    $preferredHappiness = Convert-ToNumber (Get-PropertyValue $food.Happiness "Preferred")
    if ($preferredHappiness -ne 5) {
        Add-Failure "$foodPath Happiness.Preferred must be 5 (actual: $preferredHappiness)"
    }
    $compatibleHappiness = Convert-ToNumber (Get-PropertyValue $food.Happiness "Compatible")
    if ($compatibleHappiness -ne -8) {
        Add-Failure "$foodPath Happiness.Compatible must be -8 (actual: $compatibleHappiness)"
    }

    $override = Get-PropertyValue $food.RoleOverrides "Tamed_Dragon_Frost"
    if ($null -eq $override) {
        Add-Failure "$foodPath RoleOverrides.Tamed_Dragon_Frost is missing"
    } else {
        $overrideFoods = Get-PropertyValue $override "Foods"
        Assert-ExactSingle (Get-PropertyValue $overrideFoods "Preferred") "Ingredient_Ice_Essence" "$foodPath RoleOverrides.Tamed_Dragon_Frost Foods.Preferred"
    }
}

foreach ($model in @(
    [pscustomobject]@{ Label = "standard"; Value = $standardModel },
    [pscustomobject]@{ Label = "AvatarFlight"; Value = $avatarModel }
)) {
    if ($null -eq $model.Value) {
        continue
    }
    $nodeNames = @(Get-JsonPropertyEntries $model.Value "name")
    if (-not (@($nodeNames | Where-Object { $_.Value -eq "Top Jaw" }).Count -gt 0)) {
        Add-Failure "$($model.Label) Frost Dragon model must expose a 'Top Jaw' node"
    }
}

foreach ($path in $boltPaths) {
    $interaction = $boltInteractions[$path]
    if ($null -eq $interaction) {
        continue
    }

    $targetNodes = @(Get-JsonPropertyEntries $interaction "TargetNodeName")
    if ($targetNodes.Count -eq 0) {
        Add-Failure "$path must attach its charging particle to Top Jaw"
    } elseif (@($targetNodes | Where-Object { $_.Value -ne "Top Jaw" }).Count -gt 0) {
        Add-Failure "$path must use Top Jaw for every TargetNodeName (actual: $(@($targetNodes | ForEach-Object { $_.Value }) -join ', '))"
    }

    $launchOffsets = @(Get-JsonPropertyEntries $interaction "LaunchPositionOffset")
    if ($launchOffsets.Count -ne 1) {
        Add-Failure "$path must have exactly one LaunchPositionOffset"
        continue
    }

    $offset = $launchOffsets[0].Value
    $x = Convert-ToNumber (Get-PropertyValue $offset "X")
    $y = Convert-ToNumber (Get-PropertyValue $offset "Y")
    $z = Convert-ToNumber (Get-PropertyValue $offset "Z")
    if ($x -ne 0 -or $y -ne 1.5 -or $z -ne -3.0) {
        Add-Failure "$path LaunchPositionOffset must be X 0, Y 1.5, Z -3.0 (actual: X $x, Y $y, Z $z)"
    }
    if ($y -ge 2.25) {
        Add-Failure "$path LaunchPositionOffset.Y must be lower than the old 2.25 origin (actual: $y)"
    }
    if ($z -ge 0) {
        Add-Failure "$path LaunchPositionOffset.Z must be negative/forward in AvatarFlight coordinates (actual: $z)"
    }

    $worldSounds = @(Get-JsonPropertyEntries $interaction "WorldSoundEventId" | ForEach-Object { $_.Value })
    Assert-ExactSingle $worldSounds "SFX_AH_Dragon_Frost_Frost_Bolt_Launch" "$path WorldSoundEventId"
    $localSounds = @(Get-JsonPropertyEntries $interaction "LocalSoundEventId")
    if ($localSounds.Count -ne 0) {
        Add-Failure "$path must use the Nordic Drake-style world-only projectile launch sound"
    }
}

$breathSystemId = "AH_Dragon_Frost_Freezing_Breath"
$sourceEffectId = "AH_Dragon_Frost_Freezing_Breath_Source"
foreach ($path in $breathPaths) {
    $interaction = $breathInteractions[$path]
    if ($null -eq $interaction) {
        continue
    }

    $particleObjects = @(Get-JsonObjectEntries $interaction | Where-Object {
        [string](Get-PropertyValue $_.Value "SystemId") -eq $breathSystemId
    })
    if ($particleObjects.Count -ne 1) {
        Add-Failure "$path must contain exactly one dedicated $breathSystemId particle (actual: $($particleObjects.Count))"
    }
    foreach ($particle in $particleObjects) {
        $targetNode = Get-PropertyValue $particle.Value "TargetNodeName"
        if ([string]$targetNode -ne "Top Jaw") {
            Add-Failure "$path dedicated breath particle must target Top Jaw (actual: $targetNode)"
        }
        $detached = Get-PropertyValue $particle.Value "DetachedFromModel"
        if ([string]$detached -ne "False") {
            Add-Failure "$path dedicated breath particle must keep DetachedFromModel false (actual: $detached)"
        }
        $offset = Get-PropertyValue $particle.Value "PositionOffset"
        $z = Convert-ToNumber (Get-PropertyValue $offset "Z")
        if ($null -eq $z -or $z -le 0) {
            Add-Failure "$path dedicated breath particle must use a positive local-Z mouth offset (actual: $z)"
        }
    }

    $sourceReferences = @(Get-JsonObjectEntries $interaction | Where-Object {
        [string](Get-PropertyValue $_.Value "Type") -eq "ApplyEffect" -and
            [string](Get-PropertyValue $_.Value "EffectId") -eq $sourceEffectId
    })
    if ($sourceReferences.Count -lt 3) {
        Add-Failure "$path must refresh $sourceEffectId at least three times (actual: $($sourceReferences.Count))"
    }

    $breathRoars = @(Get-JsonPropertyEntries $interaction "WorldSoundEventId" | Where-Object {
        [string]$_.Value -eq "SFX_AH_Dragon_Frost_Breath_Roar"
    })
    if ($breathRoars.Count -ne 1) {
        Add-Failure "$path must play the Nordic Drake breath roar exactly once (actual: $($breathRoars.Count))"
    }

    if ($path -eq $breathPaths[2]) {
        $parallelBranches = @()
        $rootInteractions = @(Get-PropertyValue $interaction "Interactions")
        if ($rootInteractions.Count -gt 0) {
            $parallelBranches = @(Get-PropertyValue $rootInteractions[0] "Interactions")
        }

        $damageInteractions = @()
        if ($parallelBranches.Count -gt 1) {
            $damageInteractions = @(Get-PropertyValue $parallelBranches[1] "Interactions")
        }

        $openingDelay = if ($damageInteractions.Count -gt 0) { $damageInteractions[0] } else { $null }
        $openingRefresh = if ($damageInteractions.Count -gt 1) { $damageInteractions[1] } else { $null }
        $firstSelectorIndex = -1
        for ($index = 0; $index -lt $damageInteractions.Count; $index++) {
            if ([string](Get-PropertyValue $damageInteractions[$index] "Type") -eq "Selector") {
                $firstSelectorIndex = $index
                break
            }
        }

        $openingRunTime = if ($null -ne $openingDelay) { Convert-ToNumber (Get-PropertyValue $openingDelay "RunTime") } else { $null }
        $openingType = if ($null -ne $openingDelay) { [string](Get-PropertyValue $openingDelay "Type") } else { $null }
        $refreshType = if ($null -ne $openingRefresh) { [string](Get-PropertyValue $openingRefresh "Type") } else { $null }
        $refreshEffectId = if ($null -ne $openingRefresh) { [string](Get-PropertyValue $openingRefresh "EffectId") } else { $null }
        if ($openingType -ne "Simple" -or $openingRunTime -ne 0.5 -or
            $refreshType -ne "ApplyEffect" -or $refreshEffectId -ne $sourceEffectId -or
            $firstSelectorIndex -lt 2) {
            Add-Failure "$path Avatar damage branch must apply $sourceEffectId immediately after the opening 0.5-second delay before the first Selector"
        }
    }

    $bannedReferences = @(Get-JsonScalarEntries $interaction | Where-Object { [string] $_.Value -eq "Ice_Staff" -or [string] $_.Value -eq "SFX_Staff_Ice_Shoot" })
    if ($bannedReferences.Count -gt 0) {
        Add-Failure "$path still references Ice_Staff or SFX_Staff_Ice_Shoot"
    }
}

if ($null -ne $particleSystem) {
    $systemSpawners = @(Get-JsonPropertyEntries $particleSystem "SpawnerId" | ForEach-Object { $_.Value })
    foreach ($expectedSpawner in @(
        "AH_Dragon_Frost_Freezing_Breath_Mist",
        "AH_Dragon_Frost_Freezing_Breath_Crystals"
    )) {
        if ($systemSpawners -notcontains $expectedSpawner) {
            Add-Failure "$particleSystemPath must include spawner $expectedSpawner"
        }
    }
}

foreach ($path in $spawnerPaths) {
    $spawner = $spawners[$path]
    if ($null -eq $spawner) {
        continue
    }

    $continuous = $false
    foreach ($entry in @(Get-JsonPropertyEntries $spawner "SpawnRate")) {
        if (Test-PositiveRange $entry.Value) {
            $continuous = $true
        }
    }
    if (-not $continuous) {
        Add-Failure "$path must emit continuously with a positive SpawnRate"
    }

    $forward = $false
    foreach ($entry in @(Get-JsonPropertyEntries $spawner "InitialVelocity")) {
        $speed = Get-PropertyValue $entry.Value "Speed"
        if (Test-PositiveRange $speed) {
            $forward = $true
        }
    }
    if (-not $forward) {
        Add-Failure "$path must use positive forward InitialVelocity.Speed"
    }

    $lifeMax = Convert-ToNumber (Get-PropertyValue (Get-PropertyValue $spawner "ParticleLifeSpan") "Max")
    $speedMax = Convert-ToNumber (Get-PropertyValue (Get-PropertyValue (Get-PropertyValue $spawner "InitialVelocity") "Speed") "Max")
    $maxTravel = if ($null -ne $lifeMax -and $null -ne $speedMax) { $lifeMax * $speedMax } else { 0 }
    if ($maxTravel -lt 7.5) {
        Add-Failure "$path must project at least 7.5 blocks before scaling (actual: $maxTravel)"
    }

    foreach ($axis in @("Yaw", "Pitch")) {
        $spread = Get-PropertyValue (Get-PropertyValue $spawner "InitialVelocity") $axis
        $spreadMin = Convert-ToNumber (Get-PropertyValue $spread "Min")
        $spreadMax = Convert-ToNumber (Get-PropertyValue $spread "Max")
        if ($null -eq $spreadMin -or $null -eq $spreadMax -or $spreadMin -lt -8 -or $spreadMax -gt 8) {
            Add-Failure "$path InitialVelocity.$axis must stay within -8..8 degrees for a focused long-range stream"
        }
    }
}

if ($null -ne $breathRoarSound) {
    Assert-ExactSingle (Get-PropertyValue $breathRoarSound.Layers[0] "Files") "Sounds/AnimalHusbandry/Dragon_Frost/Avatar_Flame_Breath_Roar.ogg" "$breathRoarSoundPath Layers[0].Files"
}
if ($null -ne $boltLaunchSound) {
    Assert-ExactSingle (Get-PropertyValue $boltLaunchSound.Layers[0] "Files") "Sounds/AnimalHusbandry/Dragon_Frost/Avatar_Fireball_Launch.ogg" "$boltLaunchSoundPath Layers[0].Files"
}

if ($null -ne $sourceEffect) {
    $duration = Convert-ToNumber (Get-PropertyValue $sourceEffect "Duration")
    if ($duration -ne 0.5) {
        Add-Failure "$sourceEffectPath Duration must be 0.5 seconds (actual: $duration)"
    }
    if ((Get-PropertyValue $sourceEffect "OverlapBehavior") -ne "Overwrite") {
        Add-Failure "$sourceEffectPath OverlapBehavior must be Overwrite"
    }
    $applicationEffects = Get-PropertyValue $sourceEffect "ApplicationEffects"
    if ([string](Get-PropertyValue $applicationEffects "WorldSoundEventId") -ne "SFX_Staff_Flame_Flamethrower") {
        Add-Failure "$sourceEffectPath ApplicationEffects.WorldSoundEventId must match FlamethrowerSource"
    }
    if ([string](Get-PropertyValue $applicationEffects "LocalSoundEventId") -ne "SFX_Staff_Flame_Flamethrower_Local") {
        Add-Failure "$sourceEffectPath ApplicationEffects.LocalSoundEventId must match FlamethrowerSource"
    }
    if ([string](Get-PropertyValue $sourceEffect "WorldRemovalSoundEventId") -ne "SFX_Staff_Flame_Flamethrower_End") {
        Add-Failure "$sourceEffectPath WorldRemovalSoundEventId must match FlamethrowerSource"
    }
    if ([string](Get-PropertyValue $sourceEffect "LocalRemovalSoundEventId") -ne "SFX_Staff_Flame_Flamethrower_End_Local") {
        Add-Failure "$sourceEffectPath LocalRemovalSoundEventId must match FlamethrowerSource"
    }
}

if ($failures.Count -gt 0) {
    $failures | ForEach-Object { [Console]::Error.WriteLine($_) }
    exit 1
}

Write-Host "Frost Dragon feeding and breath contract checks passed."
