param(
    [string] $Root = (Get-Location).Path
)

$ErrorActionPreference = "Stop"

$configPath = Join-Path $Root "Server/Tamework/AvatarFlight/AHAvatarFlight.json"
$rootPath = Join-Path $Root "Server/Item/RootInteractions/NPCs/Creature/AnimalHusbandry/Dragon_Frost/Root_NPC_AH_Dragon_Frost_Avatar_Frost_Bolt.json"
$interactionPath = Join-Path $Root "Server/Item/Interactions/NPCs/AnimalHusbandry/Dragon_Frost/AH_Dragon_Frost_Avatar_Frost_Bolt.json"
$nativeInteractionPath = Join-Path $Root "Server/Item/Interactions/NPCs/AnimalHusbandry/Dragon_Frost/AH_Dragon_Frost_Frost_Bolt.json"

$failures = New-Object System.Collections.Generic.List[string]

foreach ($path in @($configPath, $rootPath, $interactionPath, $nativeInteractionPath)) {
    if (-not (Test-Path -LiteralPath $path)) {
        $failures.Add("missing required asset: $path")
    }
}

if ($failures.Count -eq 0) {
    $config = Get-Content -LiteralPath $configPath -Raw | ConvertFrom-Json
    $rootAsset = Get-Content -LiteralPath $rootPath -Raw | ConvertFrom-Json
    $interaction = Get-Content -LiteralPath $interactionPath -Raw | ConvertFrom-Json
    $nativeInteraction = Get-Content -LiteralPath $nativeInteractionPath -Raw | ConvertFrom-Json

    $ability2 = $config.CombatAbilities.Ability2
    if ($null -eq $ability2 -or $ability2.RootInteraction -ne "Root_NPC_AH_Dragon_Frost_Avatar_Frost_Bolt" -or $ability2.Glyph -ne "ICE") {
        $failures.Add("Ability2 must reference the Frost Dragon AvatarFlight root with the ICE glyph")
    }
    if ($null -ne $config.CombatAbilities.Ability3) {
        $failures.Add("Ability3 must remain absent")
    }

    if (@($rootAsset.Interactions).Count -ne 1 -or $rootAsset.Interactions[0] -ne "AH_Dragon_Frost_Avatar_Frost_Bolt") {
        $failures.Add("player-safe root must resolve the AvatarFlight frost-bolt interaction")
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
}

if ($failures.Count -gt 0) {
    $failures | ForEach-Object { [Console]::Error.WriteLine($_) }
    exit 1
}

Write-Host "AvatarFlight Frost Dragon frost-bolt contract checks passed."
