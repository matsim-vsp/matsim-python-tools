#!/bin/bash

python3.9 -m venv venv
source venv/bin/activate

pip install --upgrade pip
pip install optuna geopandas rtree pygeos eclipse-sumo sumolib traci lxml optax requests tqdm sklearn

# install matsim tools
pip install "matsim-tools[scenariogen] @ git+https://github.com/matsim-vsp/matsim-python-tools.git@scenario-creation"