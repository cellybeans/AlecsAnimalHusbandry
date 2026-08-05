param(
    [string] $Root = (Get-Location).Path
)

$ErrorActionPreference = "Stop"

$templatePath = Join-Path $Root "Server/NPC/Roles/_Core/Templates/AH_Template_Dragon_Frost_Tamed.json"
$failures = New-Object System.Collections.Generic.List[string]

if (-not (Test-Path -LiteralPath $templatePath)) {
    $failures.Add("missing Frost Dragon tamed template: $templatePath")
} else {
    $template = Get-Content -LiteralPath $templatePath -Raw | ConvertFrom-Json
    $aggressiveState = @($template.Instructions[2].Instructions | Where-Object {
        $_.Sensor.Type -eq "State" -and $_.Sensor.State -eq "Aggressive" -and $_.Instructions
    })

    if ($aggressiveState.Count -ne 1) {
        $failures.Add("expected exactly one Frost Dragon Aggressive state")
    } else {
        $instructions = @($aggressiveState[0].Instructions)
        $specialCombat = @($instructions | Where-Object {
            $_.Enabled.Compute -eq "UseFrostDragonTamedCombat" -and
            $_.Instructions.Reference -eq "Component_AH_Instruction_Dragon_Frost_Tamed_Combat"
        })
        if ($specialCombat.Count -ne 1) {
            $failures.Add("Aggressive must retain the Frost Dragon tamed combat controller")
        }

        $ground = @($instructions | Where-Object {
            $_.Sensor.Sensors.Name -contains "AirborneMode" -and
            $_.Sensor.Sensors.MotionController -contains "Walk" -and
            $_.Instructions.Reference -eq "Component_Tamework_Instruction_Aggressive"
        })
        if ($ground.Count -ne 1 -or $ground[0].Instructions.Modify.DefendFollowMacroElement -ne "AH_Component_Tamework_Instruction_Follow_Large") {
            $failures.Add("Aggressive grounded path must use the large companion follow macro")
        }

        $flying = @($instructions | Where-Object {
            $_.Sensor.Sensors.Name -contains "AirborneMode" -and
            $_.Sensor.Sensors.MotionController -contains "Fly" -and
            $_.Instructions.Reference -eq "Component_Tamework_Instruction_Aggressive"
        })
        if ($flying.Count -ne 1 -or $flying[0].Instructions.Modify.DefendFollowMacroElement -ne "AH_Component_Tamework_Instruction_Follow_Frost_Dragon_Flying") {
            $failures.Add("Aggressive flying path must use the Frost Dragon flying follow macro")
        }
    }
}

if ($failures.Count -gt 0) {
    $failures | ForEach-Object { [Console]::Error.WriteLine($_) }
    exit 1
}

Write-Host "Frost Dragon aggressive behavior contract checks passed."
