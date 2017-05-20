#!/bin/bash
echo "Starting build..."
if [ -f "bin/activate" ]; then
	source bin/activate
	if [ -f "requirements.txt" ]; then
		pip install -r requirements.txt
	fi
	pyinstaller main.py --onefile -c -n cryptoprobe
	echo "Done!"
else
	echo "Error: No virtualenv found."
fi

# echo "lol"
# echo "$result"