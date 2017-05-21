echo "Starting build..."
if (test-path "Scripts/activate.ps1") 
{
	Scripts/activate.ps1
	if (test-path "requirements.txt")
	{
		pip install -r requirements.txt
	}
	python main.py
}
else { echo "Error: No virtualenv found." }