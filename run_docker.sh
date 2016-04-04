#!/bin/bash

pushd `dirname $0` > /dev/null
SCRIPTPATH=`pwd -P`
popd > /dev/null

# If you just want to run the Docker container,
run_jupyter="jupyter notebook --no-browser --port 8888 --ip=0.0.0.0 --notebook-dir=pavement"
docker run -it -p 8888:8888 -v $SCRIPTPATH:/pavement --rm --link pavement_osrm:server --name pavement_anaconda pavement/anaconda $run_jupyter

