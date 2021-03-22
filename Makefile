.PHONY: all setup lint

all:
	./scripts/process_all.sh

setup:
	# python 3.8 is required
	pip3 install -r requirements.txt

lint:
	jsonschema -i sources/ad.json sources/schema.json
	jsonschema -i sources/dating.json sources/schema.json
	jsonschema -i sources/gambling.json sources/schema.json
	jsonschema -i sources/malicious.json sources/schema.json
	jsonschema -i sources/piracy.json sources/schema.json
	jsonschema -i sources/porn.json sources/schema.json
	jsonschema -i sources/social_networks.json sources/schema.json
	./scripts/validate_source.py sources/*.json
	flake8
	pylint scripts
	isort scripts --check --diff
