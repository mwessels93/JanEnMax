SHELL := /bin/bash

# INITIALIZATION
## create the appropriate folder structure
scaffold:
	# create directory structure
	@test -d .virtualenv || mkdir -p .virtualenv
	@test -d src/python || mkdir -p src/python
	@test -d tools/scripts/hooks || mkdir -p tools/scripts/hooks
	# @test -d reports/cov || mkdir -p reports/cov
	# @test -d reports/lint || mkdir -p reports/lint
	# @test -d reports/codestyle || mkdir -p reports/codestyle
	@touch README.md

	# set up git hooks
	@test -d .git/hooks || mkdir -p .git/hooks
	@ln -sf ../../tools/scripts/hooks/pre-commit.sh .git/hooks/pre-commit
	@ln -sf ../../tools/scripts/hooks/commit-msg.sh .git/hooks/commit-msg
	@ln -sf ../../tools/scripts/hooks/pre-push.sh .git/hooks/pre-push

init: scaffold
	tools/scripts/project-variables.sh
clean:
	tools/scripts/clean.sh
doc: init
setup-dev:
	tools/scripts/dev.sh
dev-activate:
	tools/scripts/dev-activate.sh

setup: setup-dev dev-activate

# TESTING
test: test-unit test-lint
test-precommit: test-unit
test-lint:
	tools/scripts/test/test-lint.sh
test-unit:
	tools/scripts/test/test.sh
test-jenkins: init
build-jenkins: init
deploy-jenkins: init

# PACKAGING
## egg packing
build-egg:
	tools/scripts/build-egg.sh
install-egg:
	tools/scripts/install-egg.sh

## Wheel packing
build-wheel:
	tools/scripts/build-wheel.sh
install-wheel:
	tools/scripts/install-wheel.sh

## source packaging
build-sdist:
	tools/scripts/build-sdist.sh

## Debian packing
build-deb:
	tools/scripts/build-deb.sh
install-deb:
	tools/scripts/install-deb.sh

## Developing
develop:
	tools/scripts/develop.sh

# .PHONY: scaffold init test test-lint test-unit
