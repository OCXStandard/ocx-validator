# Project make file
# A self-documenting Makefile
# You can set these variables from the command line, and also
# from the environment for the first two.
SOURCE = ./resources
CONDA_ENV = validator
IMAGE = 3docx/validator
DOCKER_HUB = 3docx
CONTAINER = validator
TAG = 3.0.0rc2


# CONDA TASKS ##################################################################
# PROJECT setup using conda and powershell


conda-create:   ## Create the conda environment with a specific python version
	@conda create -n $CONDA_ENV python=3.11
	@conda activate $CONDA_ENV


conda-upd:   ## Update the conda development environment when environment.yaml has changed
	@conda env update -f environment.yml

.PHONY: conda-upd


# DOCKER TASKS ##################################################################

build:   ## Build the docker validator image using Dockerfile including the defined  resources
	@docker build . --tag $(IMAGE):$(TAG)


push:   ## Push the docker validator latest build image to dockerhub
	@docker logout
	@docker login -u $(DOCKER_HUB)
	@docker push $(DOCKER_HUB)/$(CONTAINER):$(TAG)

stop: ## Stop the running container
	@docker stop $(CONTAINER)
	@docker rm $(CONTAINER)

run:  ## Set up the container
	@docker run -d --name $(CONTAINER) -p 8080:8080  $(IMAGE):$(TAG)

all:  ## Build and run
	@make stop
	@make build
	@make tag
	@make run

test-rudder: ## Access the Rudder upload page for validating ocx-rudder-extension v1.0.0 models

	@cmd /c start "http://localhost:8080/extensions/upload"

test-ocx: ## Access the OCX upload page for validating OCX v2.8.6 models

	@cmd /c start "http://localhost:8080/ocx/upload"
.PHONY: build, run, test-rudder, test-ocx

schematron: ## Access the OCX upload page for validating OCX v2.8.6 models

	@cmd /c start "http://localhost:8080/schematronmake stop/upload"


# HELP ########################################################################


.PHONY: help
help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'

.DEFAULT_GOAL := help

#-----------------------------------------------------------------------------------------------
