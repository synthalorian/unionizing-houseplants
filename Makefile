.PHONY: install test demo run dashboard clean lint

install:
	pip install -e .

test:
	pytest tests/ -v

demo:
	python demo.py

run:
	python run.py

dashboard:
	python -m unionizing_houseplants.dashboard

lint:
	python -m flake8 unionizing_houseplants/ tests/ --max-line-length 100

clean:
	rm -rf build/ dist/ *.egg-info .pytest_cache __pycache__ .mypy_cache
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name '*.pyc' -delete
