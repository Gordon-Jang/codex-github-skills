param(
    [Parameter(Mandatory = $true)]
    [string[]]$SkillNames,

    [string]$SkillsRoot = "$HOME\.codex\skills",

    [switch]$Strict
)

$ErrorActionPreference = "Stop"

function Split-SkillNames {
    param([string[]]$Names)

    $result = @()
    foreach ($rawName in $Names) {
        $result += ($rawName -split "," | ForEach-Object { $_.Trim() } | Where-Object { $_ })
    }
    return $result
}

function Get-Frontmatter {
    param([string]$Content)

    $match = [regex]::Match($Content, "(?s)^---\s*\r?\n(?<frontmatter>.*?)\r?\n---\s*")
    if (-not $match.Success) {
        return $null
    }
    return $match.Groups["frontmatter"].Value
}

function Get-ScalarField {
    param(
        [string]$Frontmatter,
        [string]$FieldName
    )

    $escaped = [regex]::Escape($FieldName)
    $match = [regex]::Match($Frontmatter, "(?m)^$escaped\s*:\s*['""]?(?<value>[^'""`r`n]+)")
    if (-not $match.Success) {
        return ""
    }
    return $match.Groups["value"].Value.Trim()
}

function Test-CommandMention {
    param(
        [string]$Content,
        [string]$CommandName
    )

    if (-not [regex]::IsMatch($Content, "(?i)(^|[^A-Za-z0-9_.-])$([regex]::Escape($CommandName))([^A-Za-z0-9_.-]|$)")) {
        return $null
    }

    $command = Get-Command $CommandName -ErrorAction SilentlyContinue
    if ($command) {
        return "${CommandName}:ok"
    }
    return "${CommandName}:missing"
}

$rows = @()
$hasFailure = $false
$hasWarning = $false
$normalizedSkillNames = Split-SkillNames -Names $SkillNames

foreach ($name in $normalizedSkillNames) {
    $candidatePaths = @(
        (Join-Path $SkillsRoot $name),
        (Join-Path (Join-Path $SkillsRoot ".system") $name)
    )

    $skillDir = $candidatePaths | Where-Object { Test-Path -LiteralPath $_ -PathType Container } | Select-Object -First 1
    if (-not $skillDir) {
        $hasFailure = $true
        $rows += [PSCustomObject]@{
            Skill = $name
            Status = "missing"
            Path = ""
            FileCount = 0
            NameField = ""
            HasDescription = $false
            NameMatchesFolder = $false
            HasOpenAiYaml = $false
            Resources = ""
            Tools = ""
        }
        continue
    }

    $skillFile = Join-Path $skillDir "SKILL.md"
    if (-not (Test-Path -LiteralPath $skillFile -PathType Leaf)) {
        $hasFailure = $true
        $rows += [PSCustomObject]@{
            Skill = $name
            Status = "missing-skill-md"
            Path = $skillDir
            FileCount = 0
            NameField = ""
            HasDescription = $false
            NameMatchesFolder = $false
            HasOpenAiYaml = $false
            Resources = ""
            Tools = ""
        }
        continue
    }

    $content = Get-Content -LiteralPath $skillFile -Raw -Encoding UTF8
    $frontmatter = Get-Frontmatter -Content $content
    $status = "ok"

    if (-not $frontmatter) {
        $hasFailure = $true
        $status = "bad-frontmatter"
    }

    $nameField = if ($frontmatter) { Get-ScalarField -Frontmatter $frontmatter -FieldName "name" } else { "" }
    $descriptionField = if ($frontmatter) { Get-ScalarField -Frontmatter $frontmatter -FieldName "description" } else { "" }
    $hasDescription = $descriptionField.Length -gt 0
    $nameMatchesFolder = $nameField -eq (Split-Path -Leaf $skillDir)
    $openAiYaml = Join-Path (Join-Path $skillDir "agents") "openai.yaml"
    $hasOpenAiYaml = Test-Path -LiteralPath $openAiYaml -PathType Leaf

    if ($status -eq "ok" -and (-not $nameField -or -not $hasDescription)) {
        $hasFailure = $true
        $status = "missing-metadata"
    } elseif ($status -eq "ok" -and -not $nameMatchesFolder) {
        $hasWarning = $true
        $status = "name-mismatch"
    } elseif ($status -eq "ok" -and -not $hasOpenAiYaml) {
        $hasWarning = $true
        $status = "missing-openai-yaml"
    }

    $files = Get-ChildItem -LiteralPath $skillDir -Recurse -File -ErrorAction SilentlyContinue
    $resourceParts = @()
    foreach ($resourceName in @("scripts", "references", "assets", "agents")) {
        $resourcePath = Join-Path $skillDir $resourceName
        if (Test-Path -LiteralPath $resourcePath -PathType Container) {
            $count = (Get-ChildItem -LiteralPath $resourcePath -Recurse -File -ErrorAction SilentlyContinue | Measure-Object).Count
            $resourceParts += "${resourceName}:${count}"
        }
    }

    $toolParts = @()
    foreach ($commandName in @("git", "gh", "python", "npx", "uv", "markitdown", "ffmpeg")) {
        $toolStatus = Test-CommandMention -Content $content -CommandName $commandName
        if ($toolStatus) {
            $toolParts += $toolStatus
        }
    }

    $rows += [PSCustomObject]@{
        Skill = $name
        Status = $status
        Path = $skillDir
        FileCount = ($files | Measure-Object).Count
        NameField = $nameField
        HasDescription = $hasDescription
        NameMatchesFolder = $nameMatchesFolder
        HasOpenAiYaml = $hasOpenAiYaml
        Resources = ($resourceParts -join ", ")
        Tools = ($toolParts -join ", ")
    }
}

$rows | Format-Table -Wrap -AutoSize

if ($hasFailure -or ($Strict -and $hasWarning)) {
    exit 1
}
