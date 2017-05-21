echo "Starting build..."
if (test-path "Scripts/activate.ps1") 
{
	Scripts/activate.ps1
	if (test-path "requirements.txt")
	{
		pip install -r requirements.txt
	}
	pyinstaller main.py --onefile -c -n cryptoprobe
	echo "Done!"
}
else { echo "Error: No virtualenv found." }