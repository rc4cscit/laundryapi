include .env
export

# .PHONY: redis-remote
# redis-remote:
# 	redis-cli -h ${REDIS_HOST} -p ${REDIS_PORT} -a ${REDIS_PASS}

# .PHONY: seed-redis
# seed-redis:
# 	redis-cli -h ${REDIS_HOST} -p ${REDIS_PORT} -a ${REDIS_PASS} --eval ./app/redis/seed.lua

.PHONY: test
test:
	python -m pytest -v

.PHONY: fmt
fmt:
	python -m black app tests
	python -m isort app tests --profile=black

.PHONY: deploy
deploy:
	sls requirements cleanCache && sls deploy
