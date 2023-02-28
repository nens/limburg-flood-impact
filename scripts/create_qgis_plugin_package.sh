#!/bin/bash

########################################################################################################################
# Create ZIP package of the plugin ready for upload to plugin repository
########################################################################################################################

set -u # Exit if we try to use an uninitialised variable
set -e # Return early if any command returns a non-0 exit status

echo "CREATE PLUGIN"

command -v zip >/dev/null 2>&1 || { echo "I require zip but it's not installed.  Aborting." >&2; exit 1; }

PWD=`pwd`
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PLUGIN=limburg_flood_impact_plugin
SRC=$DIR/../qgis-plugin/$PLUGIN
DEST="$DIR/../qgis-plugin/build"
DEST_BUILD=$DEST/$PLUGIN

if [ ! -d "$SRC" ]; then
  echo "Missing directory $SRC"
  exit 1
fi

rm -rf $DEST_BUILD
ZIP_FILE=$DEST/"$PLUGIN.zip"
if test -f "$ZIP_FILE"; then
    rm $ZIP_FILE
fi

mkdir -p $DEST_BUILD

cp -R $SRC/* $DEST_BUILD/
find $DEST_BUILD -type l -exec unlink {} \;

find $DEST_BUILD -name \*.pyc -delete
find $DEST_BUILD -name __pycache__ -delete

cd $DEST_BUILD/..
zip -r $DEST/$PLUGIN.zip $PLUGIN --exclude *.idea*

echo "$DEST/$PLUGIN.zip created"

cd $PWD
