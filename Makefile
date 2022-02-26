# The binary to build (just the basename).
MODULE := ocx_validator


# This version-strategy uses git tags to set the version string
TAG := $(shell git describe --tags --always --dirty)

BLUE='\033[0;34m'
NC='\033[0m' # No Color

run:
	@python  $(MODULE)/app.py models/NAPA-OHCM_MID-SHIP-V286.3docx --schema  schema_versions/OCX_Schema_V286.xsd

test:
	@pytest $(MODULE)

lint:
	@echo "\n${BLUE}Running Pylint against source and test files...${NC}\n"
	@pylint --rcfile=setup.cfg **/*.py
	@echo "\n${BLUE}Running Flake8 against source and test files...${NC}\n"
	@flake8
	@echo "\n${BLUE}Running Bandit against source files...${NC}\n"
	@bandit -r --ini setup.cfg


export:
#  Have poetry export all dependencies to requirements.txt
	@echo "\n${BLUE}Exporting requirements from poetry to requirements.txt${NC}"
	@poetry export --without-hashes -o requirements.txt

# poetry update all dependencies
update:
	@echo "\n${BLUE}Updating dependencies .....${NC}"
	@poetry update

# Check the validity of the poetry.toml file
check:
	@poetry check

# Build the target using poetry
build-dev:
	@poetry build

# Publish the dist to TestPyPi
publish-test:
	@poetry publish -r testpypi

# Print the package version
version:
	@poetry version

.PHONY: clean image-clean build-prod push test

clean:
	rm -rf .pytest_cache .coverage .pytest_cache coverage.xml

