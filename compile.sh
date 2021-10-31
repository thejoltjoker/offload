# Remove old files
rm -rf dist build

# Compile app
pipenv run python setup.py py2app

# Zip and copy app to website
zip -r dist/Offload.zip dist/Offload.app
cp dist/Offload.zip ../offload_website/assets/files/Offload.zip

# Copy to Applications folder
yes | cp -rf dist/Offload.app /Applications/Offload.app
