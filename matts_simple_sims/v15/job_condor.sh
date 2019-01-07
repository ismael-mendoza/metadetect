#!/bin/bash

export OMP_NUM_THREADS=1

if [[ -n $_CONDOR_SCRATCH_DIR ]]; then
    # the condor system creates a scratch directory for us,
    # and cleans up afterward
    tmpdir=$_CONDOR_SCRATCH_DIR
    export TMPDIR=$tmpdir
else
    # otherwise use the TMPDIR
    tmpdir=$TMPDIR
    mkdir -p $tmpdir
fi

source activate bnl

echo `which python`

# about 1 to 1.6 hours per job
# args are nsims, seed, odir
python run_sim_condor.py $1 $2 $3 >& ${tmpdir}/log_$2.oe

mkdir -p $3/logs
mv ${tmpdir}/log_$2.oe $3/logs/.
