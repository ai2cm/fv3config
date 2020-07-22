envdir="${envloc}/env"
if [ -d "${envdir}" ] ; then
    pushd "${envdir}" > /dev/null
        `module load git; git pull &>/dev/null`
        if [ $? -ne 0 ] ; then
            echo "WARNING: Problem pulling the buildenv. Defaulting to offline mode."
        fi
    popd
else
    `module load git; git clone git@github.com:VulcanClimateModeling/buildenv.git ${envdir} &>/dev/null`
    if [ $? -ne 0 ] ; then
        echo "Error: Could not download the buildenv (https://github.com/C2SM-RCM/buildenv) into ${envdir}. Aborting."
        exit 1
    fi
fi
