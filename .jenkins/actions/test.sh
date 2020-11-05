#!/bin/bash -f

##################################################
# functions
##################################################

exitError()
{
    echo "ERROR $1: $3" 1>&2
    echo "ERROR     LOCATION=$0" 1>&2
    echo "ERROR     LINE=$2" 1>&2
    exit $1
}

showUsage()
{
    echo "usage: `basename $0` [-h]"
    echo ""
    echo "optional arguments:"
    echo "-h           show this help message and exit"
}

parseOptions()
{
    # process command line options
    while getopts "h" opt
    do
        case $opt in
        h) showUsage; exit 0 ;;
        \?) showUsage; exitError 301 ${LINENO} "invalid command line option (-${OPTARG})" ;;
        :) showUsage; exitError 302 ${LINENO} "command line option (-${OPTARG}) requires argument" ;;
        esac
    done

}

# echo basic setup
echo "####### executing: $0 $* (PID=$$ HOST=$HOSTNAME TIME=`date '+%D %H:%M:%S'`)"

# start timer
T="$(date +%s)"

# parse command line options (pass all of them to function)
parseOptions $*

# check presence of env directory
pushd `dirname $0` > /dev/null
envloc=`/bin/pwd`/..
popd > /dev/null

# Download the env
. ${envloc}/env.sh

# setup module environment and default queue
if [ ! -f ${envloc}/env/machineEnvironment.sh ] ; then
    echo "Error 1201 test.sh ${LINENO}: Could not find ${envloc}/env/machineEnvironment.sh"
    exit 1
fi
. ${envloc}/env/machineEnvironment.sh

# load machine dependent environment
if [ ! -f ${envloc}/env/env.${host}.sh ] ; then
    exitError 1202 ${LINENO} "could not find ${envloc}/env/env.${host}.sh"
fi
. ${envloc}/env/env.${host}.sh


# run tests
echo "### run tests"
if [ ! -f requirements_dev.txt ] ; then
    exitError 1205 ${LINENO} "could not find requirements_dev.txt, run from top directory"
fi
python3 -m venv venv
. ./venv/bin/activate
pip3 install wheel
pip3 install -r requirements_dev.txt
pip3 install -e .
pytest --junitxml results.xml tests
deactivate
\rm -rf venv

# install and run example
echo "### run install and example"
python3 -m venv venv
. ./venv/bin/activate
pip3 install wheel
pip3 install -e .
cd examples/
./create_rundir.sh
test -d example_rundir || exit 1
test -f example_rundir/input.nml || exit 1
test -f example_rundir/field_table || exit 1
test -f example_rundir/grb/seaice_newland.grb || exit 1
deactivate
\rm -rf venv

# end timer and report time taken
T="$(($(date +%s)-T))"
printf "####### time taken: %02d:%02d:%02d:%02d\n" "$((T/86400))" "$((T/3600%24))" "$((T/60%60))" "$((T%60))"

# no errors encountered
echo "####### finished: $0 $* (PID=$$ HOST=$HOSTNAME TIME=`date '+%D %H:%M:%S'`)"
exit 0

# so long, Earthling!
