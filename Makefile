all: ruff flake lint

flake:
	flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics
	flake8 astropix_analysis bin tests --count --exit-zero --max-complexity=10 --max-line-length=100 --statistics

ruff:
	ruff check astropix_analysis bin tests

lint:
	pylint astropix_analysis bin tests \
		--disable too-many-ancestors \
		--disable too-many-arguments \
		--disable too-many-function-args \
		--disable too-many-instance-attributes \
		--disable c-extension-no-member \
		--disable use-dict-literal \
		--disable too-many-positional-arguments \
		--disable too-many-public-methods

test:
	python -m pytest tests -s

html:
	cd docs; make html

clean:
	rm -rf astropix_analysis/__pycache__ tests/__pycache__ .pytest_cache

cleandoc:
	cd docs; make clean

cleanall: clean cleandoc
