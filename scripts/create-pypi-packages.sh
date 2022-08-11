ROOT_PATH=$(dirname "$0")
DIST_PATH=$(readlink -f "$ROOT_PATH/../dist")

$ROOT_PATH/pack.sh

echo $DIST_PATH
pip wheel setup/gui --no-deps --wheel-dir=$DIST_PATH
pip wheel setup/lib --no-deps --wheel-dir=$DIST_PATH
