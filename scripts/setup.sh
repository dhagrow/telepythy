ROOT_PATH=$(dirname "$0")
DIST_PATH=$(readlink -f "$ROOT_PATH/../dist")
echo $DIST_PATH
python setup/gui/setup.py sdist --dist-dir=$DIST_PATH
python setup/lib/setup.py sdist --dist-dir=$DIST_PATH
