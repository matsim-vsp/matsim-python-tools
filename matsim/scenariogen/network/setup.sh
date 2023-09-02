#!/bin/bash

python3.9 -m venv env
source env/bin/activate

pip install --upgrade pip
pip install optuna geopandas rtree pygeos eclipse-sumo sumolib traci lxml optax requests tqdm

# install matsim tools
pip install "https://github.com/matsim-vsp/matsim-python-tools/archive/refs/heads/scenario-creation.zip"