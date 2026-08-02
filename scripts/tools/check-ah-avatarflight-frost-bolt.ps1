param(
    [string] $Root = (Get-Location).Path
)

$ErrorActionPreference = "Stop"

$configPath = Join-Path $Root "Server/Tamework/AvatarFlight/AHAvatarFlight.json"
$rootPath = Join-Path $Root "Server/Item/RootInteractions/NPCs/Creature/AnimalHusbandry/Dragon_Frost/Root_NPC_AH_Dragon_Frost_Avatar_Frost_Bolt.json"
$interactionPath = Join-Path $Root "Server/Item/Interactions/NPCs/AnimalHusbandry/Dragon_Frost/AH_Dragon_Frost_Avatar_Frost_Bolt.json"
$nativeInteractionPath = Join-Path $Root "Server/Item/Interactions/NPCs/AnimalHusbandry/Dragon_Frost/AH_Dragon_Frost_Frost_Bolt.json"
$breathRootPath = Join-Path $Root "Server/Item/RootInteractions/NPCs/Creature/AnimalHusbandry/Dragon_Frost/Root_NPC_AH_Dragon_Frost_Avatar_Freezing_Breath.json"
$breathInteractionPath = Join-Path $Root "Server/Item/Interactions/NPCs/AnimalHusbandry/Dragon_Frost/AH_Dragon_Frost_Avatar_Freezing_Breath.json"

$failures = New-Object System.Collections.Generic.List[string]

function Test-JsonEquivalent($expected, $actual, [string] $path) {
    if ($expected -is [System.Management.Automation.PSCustomObject]) {
        $expectedProperties = @($expected.PSObject.Properties.Name | Sort-Object)
        $actualProperties = @($actual.PSObject.Properties.Name | Sort-Object)
        if (@(Compare-Object $expectedProperties $actualProperties).Count -ne 0) {
            $failures.Add("${path}: property set differs from the native frost bolt")
            return
        }
        foreach ($property in $expectedProperties) {
            Test-JsonEquivalent $expected.$property $actual.$property "$path.$property"
        }
        return
    }

    if ($expected -is [System.Collections.IEnumerable] -and $expected -isnot [string]) {
        $expectedItems = @($expected)
        $actualItems = @($actual)
        if ($expectedItems.Count -ne $actualItems.Count) {
            $failures.Add("${path}: array length differs from the native frost bolt")
            return
        }
        for ($index = 0; $index -lt $expectedItems.Count; $index++) {
            Test-JsonEquivalent $expectedItems[$index] $actualItems[$index] "$path[$index]"
        }
        return
    }

    if ($expected -ne $actual) {
        $failures.Add("${path}: value differs from the native frost bolt")
    }
}

foreach ($path in @($configPath, $rootPath, $interactionPath, $nativeInteractionPath, $breathRootPath, $breathInteractionPath)) {
    if (-not (Test-Path -LiteralPath $path)) {
        $failures.Add("missing required asset: $path")
    }
}

if ($failures.Count -eq 0) {
    $config = Get-Content -LiteralPath $configPath -Raw | ConvertFrom-Json
    $rootAsset = Get-Content -LiteralPath $rootPath -Raw | ConvertFrom-Json
    $interaction = Get-Content -LiteralPath $interactionPath -Raw | ConvertFrom-Json
    $nativeInteraction = Get-Content -LiteralPath $nativeInteractionPath -Raw | ConvertFrom-Json
    $breathRootAsset = Get-Content -LiteralPath $breathRootPath -Raw | ConvertFrom-Json

    $combatAbilityNames = @($config.CombatAbilities.PSObject.Properties.Name | Sort-Object)
    if ($combatAbilityNames.Count -ne 2 -or $combatAbilityNames[0] -ne "Ability2" -or $combatAbilityNames[1] -ne "Ability3") {
        $failures.Add("CombatAbilities must contain exactly Ability2 and Ability3")
    }
    $ability2 = $config.CombatAbilities.Ability2
    if ($null -eq $ability2 -or $ability2.RootInteraction -ne "Root_NPC_AH_Dragon_Frost_Avatar_Frost_Bolt" -or $ability2.Glyph -ne "ICE") {
        $failures.Add("Ability2 must reference the Frost Dragon AvatarFlight root with the ICE glyph")
    }
    $ability3 = $config.CombatAbilities.Ability3
    if ($null -eq $ability3 -or $ability3.RootInteraction -ne "Root_NPC_AH_Dragon_Frost_Avatar_Freezing_Breath" -or $ability3.Glyph -ne "FROST") {
        $failures.Add("Ability3 must reference the Frost Dragon AvatarFlight freezing-breath root with the FROST glyph")
    }

    if (@($rootAsset.Interactions).Count -ne 1 -or $rootAsset.Interactions[0] -ne "AH_Dragon_Frost_Avatar_Frost_Bolt") {
        $failures.Add("player-safe root must resolve the AvatarFlight frost-bolt interaction")
    }
    if (@($breathRootAsset.Interactions).Count -ne 1 -or $breathRootAsset.Interactions[0] -ne "AH_Dragon_Frost_Avatar_Freezing_Breath") {
        $failures.Add("player-safe breath root must resolve the AvatarFlight freezing-breath interaction")
    }

    $launchStep = @($interaction.Interactions | Where-Object { $_.Type -eq "TameworkLaunchProjectile" })
    if ($launchStep.Count -ne 1) {
        $failures.Add("AvatarFlight frost bolt must have exactly one TameworkLaunchProjectile step")
    } else {
        if ($launchStep[0].LookTargetDistance -ne 48.0) {
            $failures.Add("AvatarFlight frost bolt must use LookTargetDistance 48.0")
        }
        if ($null -ne $launchStep[0].TargetSlot) {
            $failures.Add("AvatarFlight frost bolt must not use TargetSlot")
        }
    }

    $nativeLaunchStep = @($nativeInteraction.Interactions | Where-Object { $_.Type -eq "TameworkLaunchProjectile" })
    if ($nativeLaunchStep.Count -ne 1 -or $nativeLaunchStep[0].TargetSlot -ne "LockedTarget") {
        $failures.Add("native NPC frost bolt must retain LockedTarget targeting")
    }

    $playerComparable = $interaction | ConvertTo-Json -Depth 100 | ConvertFrom-Json
    $nativeComparable = $nativeInteraction | ConvertTo-Json -Depth 100 | ConvertFrom-Json
    $playerComparable.PSObject.Properties.Remove("`$Comment")
    $nativeComparable.PSObject.Properties.Remove("`$Comment")
    $nativeComparableLaunchStep = @($nativeComparable.Interactions | Where-Object { $_.Type -eq "TameworkLaunchProjectile" })
    $nativeComparableLaunchStep[0].PSObject.Properties.Remove("TargetSlot")
    $nativeComparableLaunchStep[0] | Add-Member -NotePropertyName "LookTargetDistance" -NotePropertyValue 48.0
    Test-JsonEquivalent $nativeComparable $playerComparable "frost-bolt sequence"
}

if ($failures.Count -gt 0) {
    $failures | ForEach-Object { [Console]::Error.WriteLine($_) }
    exit 1
}

Write-Host "AvatarFlight Frost Dragon combat-ability contract checks passed."
