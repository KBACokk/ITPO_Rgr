WEEK ?= 17

.PHONY: test
test:
	pytest tests/test_week_$(WEEK).py
