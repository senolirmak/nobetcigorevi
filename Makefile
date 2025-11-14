.PHONY: install run package clean

install:
	pip install -e .

run:
	python nobetcigorevi/src/main.py

package:
	python setup.py sdist bdist_wheel

clean:
	rm -rf build dist *.egg-info
