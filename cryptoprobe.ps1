echo "Starting PowerShell..."
if (test-path "cryptoprobe.exe") { .\cryptoprobe.exe }
else { echo "Error: No cryptoprobe.exe found." }