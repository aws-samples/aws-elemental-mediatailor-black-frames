# import config.
# You can change the default config with `make cnf="config_special.env" build`
cnf ?= config.env
include $(cnf)
export $(shell sed 's/=.*//' $(cnf))

# import deploy config
# You can change the default deploy config with `make dpl="deploy_special.env" release`
dpl ?= deploy.env
include $(dpl)
export $(shell sed 's/=.*//' $(dpl))

# grep the version from the mix file
VERSION=$(shell ./version.sh)


# HELP
# This will output the help for each task
# thanks to https://marmelab.com/blog/2016/02/29/auto-documented-makefile.html
.PHONY: help

help: ## This help.
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)

.DEFAULT_GOAL := help


# DOCKER TASKS
# Build the container
build: ## Build the container
	docker build -t $(APP_NAME) .

build-nc: ## Build the container without caching
	docker build --no-cache -t $(APP_NAME) .

run: ## Run container making use of configs in `config.env`
	docker run -i -t --rm --env-file=./config.env --name="$(APP_NAME)" $(APP_NAME)

run-i: ## Run container interactively
	docker run -i -t --rm --env-file=./config.env --name="$(APP_NAME)" --entrypoint /bin/bash $(APP_NAME)

run-c9: ## Run container in Cloud9 IDE with configs in `config.env`
	docker run -i -t --rm --env-file=./config.env \
	-v "$(HOME)"/.aws:/root/.aws \
	--name="$(APP_NAME)" $(APP_NAME)

run-c9-i: ## Run container in Cloud9 IDE interactively wirh configs in `config.env`
	docker run -i -t --rm --env-file=./config.env \
	-v "$(HOME)"/.aws:/root/.aws \
	--name="$(APP_NAME)" --entrypoint /bin/bash $(APP_NAME)
	
run-c9-i-mount: ## Run container in Cloud9 IDE interactively wirh configs in `config.env`
	docker run -i -t --rm --env-file=./config.env \
	-v "$(HOME)"/.aws:/root/.aws \
	-v /tmp:/tmp/workdir/assets \
	--name="$(APP_NAME)" --entrypoint /bin/bash $(APP_NAME)

test-ffmpeg-black-frames:
	@cp ../../assets/bbb_short.mp4 /tmp/
	docker run -i -t --rm \
	-v /tmp:/tmp/workdir/assets \
	--name="$(APP_NAME)" --entrypoint "ffmpeg" \
	$(APP_NAME) -i /tmp/workdir/assets/bbb_short.mp4 -vf blackdetect=d=0.1:pix_th=.1 -f rawvideo -y /dev/null
	
test-ffmpeg-license:
	@docker run -i -t --rm --env-file=./config.env \
	-v "$(HOME)"/.aws:/root/.aws \
	-v /tmp:/tmp/workdir/assets \
	--entrypoint "ffmpeg" \
	--name="$(APP_NAME)" $(APP_NAME) -L
	
run-c9-dev: ## Run container in Cloud9 IDE interactively wirh configs in `config.env`
	docker run -i -t --rm --env-file=./config.env \
	-v "$(HOME)"/.aws:/root/.aws \
	-v "$(PWD)"/task:/tmp/workdir/task \
	--name="$(APP_NAME)" --entrypoint /bin/bash $(APP_NAME)

up: build run-c9 ## Build and run container as configured in `config.env` (Alias to run)

stop: ## Stop and remove a running container
	docker stop $(APP_NAME); docker rm $(APP_NAME)

release: build-nc publish ## Make a release by building and publishing the `{version}` ans `latest` tagged containers to ECR

# Docker publish
publish: repo-login publish-latest publish-version ## Publish the `{version}` ans `latest` tagged containers to ECR

publish-latest: tag-latest ## Publish the `latest` taged container to ECR
	@echo 'publish latest to $(DOCKER_REPO)'
	docker push $(DOCKER_REPO)/$(APP_NAME):latest

publish-version: tag-version ## Publish the `{version}` taged container to ECR
	@echo 'publish $(VERSION) to $(DOCKER_REPO)'
	docker push $(DOCKER_REPO)/$(APP_NAME):$(VERSION)

# Docker tagging
tag: tag-latest tag-version ## Generate container tags for the `{version}` and `latest` tags

tag-latest: ## Generate container `{version}` tag
	@echo 'create tag latest'
	docker tag $(APP_NAME) $(DOCKER_REPO)/$(APP_NAME):latest

tag-version: ## Generate container `latest` tag
	@echo 'create tag $(VERSION)'
	docker tag $(APP_NAME) $(DOCKER_REPO)/$(APP_NAME):$(VERSION)

# HELPERS

# generate script to login to aws docker repo
CMD_REPOLOGIN := "eval $$\( aws ecr"
ifdef AWS_CLI_PROFILE
CMD_REPOLOGIN += " --profile $(AWS_CLI_PROFILE)"
endif
ifdef AWS_CLI_REGION
CMD_REPOLOGIN += " --region $(AWS_CLI_REGION)"
endif
CMD_REPOLOGIN += " get-login --no-include-email \)"

# login to AWS-ECR
repo-login: ## Auto login to AWS-ECR unsing aws-cli
	@eval $(CMD_REPOLOGIN)

version: ## Output the current version
	@echo $(VERSION)
