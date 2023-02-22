PWD=`pwd`
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PYTHON_PACKAGE_DIR=python-package
PACKAGE_DIR=$DIR/../$PYTHON_PACKAGE_DIR
DEST_BUILD="$PACKAGE_DIR/build"

#render rst file with readme for package - needs Pandoc
pandoc --to=rst -o $PACKAGE_DIR/README.rst ../README.md

# remove build dir to avoid having multiple versions there
rm -rf DEST_BUILD

# build python package and upload to PyPi - authentication for PyPi needs to be set
cd $PACKAGE_DIR
python3 -m build
twine check dist/*
python3 -m twine upload dist/*

# copy whl file to QGIS plugin directory to keep python package and qgis plugin in sync
QGIS_DEP_DIR=$PACKAGE_DIR/../qgis-plugin/limburg_flood_impact_plugin/deps
rm $QGIS_DEP_DIR/*
cp dist/limburg_flood_impact-*.whl $QGIS_DEP_DIR