DOCKER_NAME=thoyo/synthetic_aperture_random
VERSION=1.0.0
CONNECTOR_CONTAINER_NAME=synthetic_aperture_random
DOCKER_NAME_FULL=$(DOCKER_NAME):$(VERSION)
DOCKER_LOCALHOST=$(shell ip addr show docker0 | grep -Po 'inet \K[\d.]+')

show_version:
	@echo $(VERSION)

clean:
	@find . -iname "*~" | xargs rm 2>/dev/null || true
	@find . -iname "*.pyc" | xargs rm 2>/dev/null || true
	@find . -iname "build" | xargs rm -rf 2>/dev/null || true

build: clean
	@docker build -t $(DOCKER_NAME_FULL) .

run: build
	@docker run -it --name $(CONNECTOR_CONTAINER_NAME) \
	--rm $(DOCKER_NAME_FULL) "/opt/twitter_bot/scripts/run"

publish: build
	@docker push $(DOCKER_NAME_FULL)
