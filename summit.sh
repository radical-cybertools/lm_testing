module use    /gpfs/alpine/stf010/world-shared/naughton/olcf/summit/modulefiles
module unload xalt spectrum-mpi
module load   gcc/6.4.0
module load   prrte/master
export PRRTE_PREFIX=$PRRTE_DIR
