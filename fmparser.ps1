# This script reads in the options to start the tool
# it sets the environment variables for Docker Compose
# and then starts Docker Compose

# environment variables for Docker:
# - INPUT_PATH
# - OUTPUT_PATH
# - FLUSH
# - REPORT
# - WITH_IMAGES

<#
.SYNOPSIS
    Parses a Foremost directory and generates a report.
.DESCRIPTION
    This tool reads in a Foremost input directory, parses its content and metadata and generates a report in the output directory.
    If --store option is not included, all data is deleted from the database afterwards.
    NOTE: The Foremost audit file must be named 'audit.txt'.
    NOTE: This script only works with PowerShell 6 or 7 (PowerShell Core)
.PARAMETER InputPath
    Foremost input directory (absolute path) [required]
.PARAMETER OutputPath
    Report output directory (absolute path) [required]
.PARAMETER Report
    Report format (supported: json) [default: json]
.PARAMETER Flush
    Delete Docker persistent volumes and output directory contents before startup [default: false]
.PARAMETER Store
    Store all parsed images in the database [default: false]
.PARAMETER WithImages
    Include image files in the report (jpg, jpeg, png, gif, webp, svg) [default: false]
#>

param(
    [Alias("i")]
    [Parameter(Position=0,Mandatory=$true,HelpMessage="Foremost input directory (absolute path)")]
    [ValidateNotNullOrEmpty()]
    [string]$InputPath,

    [Alias("o")]
    [Parameter(Position=1,Mandatory=$true,HelpMessage="Report output directory (absolute path)")]
    [ValidateNotNullOrEmpty()]
    [string]$OutputPath,

    [Alias("r")]
    [Parameter(Mandatory=$false,HelpMessage="Report format (supported: json) [default: json]")]
    [ValidateSet("json")]
    [string]$Report = "json",
    
    [Alias("f")]
    [Parameter(Mandatory=$false,HelpMessage="Delete Docker persistent volumes and output directory contents before startup")]
    [switch]$Flush = $false,

    [Alias("s")]
    [Parameter(Mandatory=$false,HelpMessage="Store all parsed images in the database [default: false]")]
    [switch]$Store = $false,

    [Parameter(Mandatory=$false,HelpMessage="Include image files in the report (jpg, jpeg, png, gif, webp, svg) [default: false]")]
    [switch]$WithImages = $false
)

# validate input and output directory provided by user
# check if path is absolute and dir exists and is readable
function Test-PathParameters {
    param(
        [Parameter(Mandatory=$true)]
        [string]$Path,

        [Parameter(Mandatory=$false)]
        [bool]$IsOutput = $false
    )

    # check for absolute path
    if (-not ($Path.StartsWith("/") -or $Path -match "^[a-zA-Z]:\\")) {
        throw "Path '$Path' needs to be absolute."
    }

    # check if dir exists
    if (-not (Test-Path -Path $Path -PathType Container)) {
        throw "Path '$Path' does not exist or is not a directory."
    }

    # check if dir is readable
    try {
        Get-ChildItem -LiteralPath $Path -ErrorAction Stop | Out-Null
    }
    catch {
        throw "Path '$Path' is not readable."
    }

    if ($IsOutput) {
        try {
            $tempFile = Join-Path -Path $Path -ChildPath ([System.IO.Path]::GetRandomFileName())
            $null = New-Item -Path $tempFile -ItemType File -Force -ErrorAction Stop
            $null = Remove-Item -Path $tempFile -Force
        } catch {
            throw "Path '$Path' is not writeable."
        }
    }
}

# check that there are input and output paths
if (-not $InputPath) { throw "Input parameter is required." }
if (-not $OutputPath) { throw "Output parameter is required." }

# validate the paths provided
Test-PathParameters -Path $InputPath -IsOutput $false
Test-PathParameters -Path $OutputPath -IsOutput $true

# clear environment variables
Set-Content -Path .env -Value ''

# set Docker environment variables
Add-Content -Path ".env" -Value "INPUT_PATH=$InputPath"
Add-Content -Path ".env" -Value "OUTPUT_PATH=$OutputPath"
Add-Content -Path ".env" -Value "REPORT=$Report"
Add-Content -Path ".env" -Value "IMAGES=$($WithImages.IsPresent)"

# if flush, flush the Docker data and output dir data
if ($Flush.IsPresent) {
    docker compose down -v

    Write-Host "Clearing output folder: $OutputPath"
    Get-ChildItem -Path $OutputPath -Recurse -Force | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
    Write-Host "Database and files flushed."
}

# for now, make sure there is an audit.txt in the Foremost folder.
$fileName = "audit.txt"
$filePath = Join-Path -Path $InputPath -ChildPath $fileName

if (-not (Test-Path $filePath)) {
    throw "Error: audit.txt not found in input directory '$InputPath'."
}

# ask if .DS_Store files should be removed or kept 
# (just in case some insane person uses PowerShell on MacOS)
if ([System.Runtime.InteropServices.RuntimeInformation]::IsOSPlatform([System.Runtime.InteropServices.OSPlatform]::OSX)) {
    $response = Read-Host "Do you want to remove .DS_Store files in the input folder? (Y/n)"

    # enter means yes
    if ([string]::IsNullOrWhiteSpace($response)) {
        $response = "Y"
    }

    # check if input dir is writeable, if not, skip
    if ($response -match "^(?i)y") {
        try {
            Write-Host "Attempting to remove all .DS_Store files in '$InputPath'."
            Get-ChildItem -Path $InputPath -Recurse -Force -Filter ".DS_Store" | Remove-Item -Force -ErrorAction Stop
            Write-Host ".DS_Store files removed."
        } catch {
            Write-Host "Warning: The folder '$InputPath' is not writeable."
            $response = Read-Host "Do you want to continue anyway or abort? (C to continue / A to abort) [A]"

            # enter means abort
            if ([string]::IsNullOrWhiteSpace($response)) {
                $response = "A"
            }

            if ($response -match "^(?i)a") {
                throw "Aborting script."
            }
            else {
                Write-Host "Skipping .DS_Store removal and continuing..."
            }
        }
    }
    else {
        Write-Host "Keeping .DS_Store files."
    }
}

## create the password file for the db
$dirName = "db"
$fileName = "password.txt"

# first, test if the dir for the file exists
# if not, create it
$dirPath = Join-Path -Path $PSScriptRoot -ChildPath $dirName
if (-not (Test-Path $dirPath -PathType Container)) {
    try {
        $null = New-Item -Path $dirPath -ItemType Directory -Force -ErrorAction Stop
    }
    catch {
        throw "Could not create password file. Aborting."
    }
}

# check if password file exists
# ask user for password and store
$filePath = Join-Path -Path $dirPath -ChildPath $fileName
if (-not (Test-Path $filePath)) {
    try {
        $response = Read-Host "No password file found. Please enter a password for the database:" -AsSecureString
        $ptr = [System.Runtime.InteropServices.Marshal]::SecureStringToBSTR($response)
        $plainTextResponse = [System.Runtime.InteropServices.Marshal]::PtrToStringBSTR($ptr)
        [System.Runtime.InteropServices.Marshal]::ZeroFreeBSTR($ptr)

        $plainTextResponse | Out-File -FilePath $filePath -Encoding UTF8 -Force
        Write-Host "Password file created at '$filePath'"
    }
    catch {
        throw "Could not create password file. Aborting."
    }
}

# set correct permissions (read/write)
try {
    if ($isWindows) {
        $acl = Get-Acl $filePath
        $accessRule = New-Object System.Security.AccessControl.FileSystemAccessRule("$env:USERNAME", "Read,Write", "Allow")
        $acl.SetAccessRule($accessRule)
        Set-Acl -Path $filePath -AclObject $acl
    }
    else {
        chmod 600 $filePath
    }
    Write-Host "Set access permissions for password file."
}
catch {
    throw "Could not set access permissions for database password file."
}

# start the parser now
Write-Host "Starting Docker now..."
docker compose run --build --rm backend

if (-not $Store.IsPresent) {
    Write-Host "Deleting Docker volumes."
    docker compose down -v
    Write-Host "Cleanup finished."
}
