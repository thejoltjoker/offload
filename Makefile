# Offload build
WEBSITE_ASSETS ?= ../offload_website/assets/files
APPLICATIONS  ?= /Applications

.PHONY: clean build zip deploy-website install all

clean:
	rm -rf dist build

build: clean
	pipenv run python setup.py py2app

zip: build
	zip -r dist/Offload.zip dist/Offload.app

deploy-website: zip
	cp dist/Offload.zip $(WEBSITE_ASSETS)/Offload.zip

install: build
	yes | cp -rf dist/Offload.app $(APPLICATIONS)/Offload.app

# Full flow: clean, build, zip, copy to website and Applications
all: build
	zip -r dist/Offload.zip dist/Offload.app
	cp dist/Offload.zip $(WEBSITE_ASSETS)/Offload.zip
	yes | cp -rf dist/Offload.app $(APPLICATIONS)/Offload.app
