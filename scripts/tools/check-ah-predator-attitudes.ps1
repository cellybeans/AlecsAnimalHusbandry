param(
    [string] $Root = (Get-Location).Path
)

$ErrorActionPreference = "Stop"
$failures = New-Object System.Collections.Generic.List[string]

$groupPath = Join-Path $Root "Server/NPC/Attitude/Roles/AH_Predator_Tamed.json"
$frostTemplatePath = Join-Path $Root "Server/NPC/Roles/_Core/Templates/AH_Template_Dragon_Frost_Tamed.json"
$frostRolePath = Join-Path $Root "Server/NPC/Roles/Creature/Mythic/Tamed/Tamed_Dragon_Frost.json"

foreach ($path in @($groupPath, $frostTemplatePath, $frostRolePath)) {
    if (-not (Test-Path -LiteralPath $path)) {
        $failures.Add("missing predator-attitude asset: $path")
    }
}

if ($failures.Count -eq 0) {
    $group = Get-Content -LiteralPath $groupPath -Raw | ConvertFrom-Json
    $requiredHostileGroups = @(
        "Aggressive", "Predators", "PredatorsBig", "Undead", "Void",
        "Trork", "Goblin", "Outlander", "Scarak", "Vermin",
        "Spiders", "Scorpions", "Snakes"
    )
    foreach ($hostileGroup in $requiredHostileGroups) {
        if ($group.Groups.Hostile -notcontains $hostileGroup) {
            $failures.Add("AH_Predator_Tamed must treat $hostileGroup as hostile")
        }
    }

    foreach ($friendlyGroup in @("Self", "AH_Predator_Tamed", "AH_Livestock_Tamed")) {
        if ($group.Groups.Friendly -notcontains $friendlyGroup) {
            $failures.Add("AH_Predator_Tamed must keep $friendlyGroup friendly")
        }
    }

    $frostTemplate = Get-Content -LiteralPath $frostTemplatePath -Raw | ConvertFrom-Json
    $frostRole = Get-Content -LiteralPath $frostRolePath -Raw | ConvertFrom-Json
    if ($frostTemplate.Parameters.AttitudeGroup.Value -ne "AH_Predator_Tamed") {
        $failures.Add("Frost Dragon template must default to AH_Predator_Tamed")
    }
    if ($frostRole.Modify.AttitudeGroup -ne "AH_Predator_Tamed") {
        $failures.Add("Frost Dragon role must use AH_Predator_Tamed")
    }

    $predatorRoles = Get-ChildItem -LiteralPath (Join-Path $Root "Server/NPC/Roles") -Recurse -Filter "*.json" |
        ForEach-Object { Get-Content -LiteralPath $_.FullName -Raw | ConvertFrom-Json } |
        Where-Object { $_.Reference -eq "AH_Template_Predator_Tamed" }
    foreach ($role in $predatorRoles) {
        if ($null -ne $role.Modify.AttitudeGroup -and $role.Modify.AttitudeGroup -ne "AH_Predator_Tamed") {
            $failures.Add("predator role overrides the dedicated predator attitude group")
        }
    }
}

if ($failures.Count -gt 0) {
    $failures | ForEach-Object { [Console]::Error.WriteLine($_) }
    exit 1
}

Write-Host "Animal Husbandry predator attitude contract checks passed."
