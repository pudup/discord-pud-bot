#!/usr/bin/env bash
set -euo pipefail

echo "Creating clean venv for pip-tools…"
python -m venv venvd
source venvd/bin/activate

pip install --upgrade pip-tools

if [ ! -f requirements.in ]; then
    echo "Creating requirements.in from requirements.txt"
    sed -E 's/(==|>=|<=|~=|<|>).*$//' requirements.txt \
        | grep -v '^\s*$' \
        > requirements.in
fi

echo "Compiling requirements.txt with pip-tools…"
pip-compile --upgrade requirements.in

deactivate
rm -rf venvd

echo "Done"