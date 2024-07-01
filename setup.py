import pathlib

from setuptools import setup, find_packages

# The directory containing this file
HERE = pathlib.Path(__file__).parent

# The text of the README file
README = (HERE / "README.md").read_text()
VERSION = (HERE / "VERSION").read_text()

# This call to setup() does all the work
setup(
    version=VERSION,
    name="matsim-tools",
    description="MATSim Agent-Based Transportation Simulation Framework - official python tools",
    long_description_content_type="text/markdown",
    url="https://github.com/matsim-vsp/matsim-python-tools",
    author="VSP-Berlin",
    author_email="charlton@tu-berlin.de",
    license="GPLv3",
    classifiers=[
        "License :: OSI Approved :: GNU General Public License (GPL)",
        "Programming Language :: Python :: 3",
    ],
    packages=["matsim"] + ["matsim." + x for x in find_packages(where="matsim")],
    install_requires=[
        "protobuf >= 3.20.0",
        "xopen >= 1.7.0",
        "pandas >= 2.1.0",
    ],
    extras_require={
        'calibration': ["optuna >= 3.5.0", "shapely >= 1.8.0", "geopandas >= 1.0.0", "scikit-learn"],
        # m2cgen has problems with newer xgb, see this issue
        # https://github.com/BayesWitnesses/m2cgen/issues/581
        'scenariogen': ["sumolib", "traci", "lxml", "optax", "requests", "tqdm", "scikit-learn", "xgboost==1.7.1", "lightgbm",
                        "sklearn-contrib-lightning", "numpy", "sympy", "m2cgen", "shapely", "optuna"],
        'viz': ["dash", "plotly.express", "dash_cytoscape", "dash_bootstrap_components"]
    },
    tests_require=["assertpy", "pytest", "scipy"],
    entry_points={
        'console_scripts': [
            'matsim-tools=matsim.cli.main:main',
            'matsim-scenariogen=matsim.scenariogen:main',
            'matsim-calibration=matsim.calibration:main',
            'matsim-viz=matsim.viz:main',
        ]
    },
    long_description=README,
)
