# Get the real path of this script
$ScriptPath = $MyInvocation.MyCommand.Path
$ScriptDir = Split-Path -Parent $ScriptPath

# Change to the actual directory where the script is located
Set-Location -Path $ScriptDir

# Create and activate Python virtual environment
if (-not (Test-Path -Path ".venv")) {
    Write-Host "Creating virtual environment..."
    python -m venv .venv
    
    # Activate virtual environment (PowerShell style)
    & .\.venv\Scripts\Activate.ps1
    
    # Install dependencies
    pip install -r requirements.txt
} else {
    # Activate virtual environment (PowerShell style)
    & .\.venv\Scripts\Activate.ps1
}

# Start the Flask server for authentication
flask --app src/main run
