#!/bin/sh
# test the correct startup of mixed OpenMP / MPI / CPU / GPU tasks

# basic information
ARG=$1
PID=$$
NODE=$(hostname)

# get MPI rank
MPI_RANK=""
test -z "$MPI_RANK" && MPI_RANK="$ALPS_APP_PE"
test -z "$MPI_RANK" && MPI_RANK="$PMIX_RANK"
test -z "$MPI_RANK" && MPI_RANK="$PMI_RANK"
test -z "$MPI_RANK" && MPI_RANK="0"

# obtain number of threads
THREAD_NUM=""
test -z "$THREAD_NUM" && THREAD_NUM="$ALPS_APP_DEPTH"
test -z "$THREAD_NUM" && THREAD_NUM="$OMP_NUM_THREADS"

# obtain info about CPU pinning
CPU_MASK=$(cat /proc/$PID/status \
        | grep -i 'Cpus_allowed:' \
        | cut -f 2 -d ':' \
        | xargs -n 1 echo \
        | sed -e 's/,//g' \
        | tr 'a-f' 'A-F')

CPU_BITS=$(echo "obase=2; ibase=16; $CPU_MASK" | \bc)
CPU_BLEN=$(echo $CPU_BITS | wc -c)
CPU_NBITS=$(cat /proc/cpuinfo | grep processor | wc -l)
while test "$CPU_BLEN" -le "$CPU_NBITS"
do
    CPU_BITS="0$CPU_BITS"
    CPU_BLEN=$((CPU_BLEN+1))
done

# same information about GPU pinning
# (assume we have no more GPUs than cores)
GPU_INFO=""
test -z "$GPU_INFO" && GPU_INFO="$CUDA_VISIBLE_DEVICES"
test -z "$GPU_INFO" && GPU_INFO="$GPU_DEVICE_ORDINAL"
GPU_INFO=$(echo " $GPU_INFO " | tr ',' ' ')

GPU_NBITS=$(lspci | grep " VGA " | wc -l)
GPU_BITS=''
n=0
while test "$n" -lt "$GPU_NBITS"
do
    if echo "$GPU_INFO" | grep -e " $n " >/dev/null
    then
        GPU_BITS="1$GPU_BITS"
    else
        GPU_BITS="0$GPU_BITS"
    fi
    n=$((n+1))
done

# redireect js_task_info to stderr (if available, i.e. on summit)
/opt/ibm/spectrum_mpi/jsm_pmix/bin/js_task_info "$TGT.info" 1>&2

PREFIX="$MPI_RANK"
test -z "$PREFIX" && PREFIX='0'

# echo "$PREFIX : PID     : $PID"

echo "$PREFIX : NODE    : $NODE"
echo "$PREFIX : CPUS    : $CPU_BITS"
echo "$PREFIX : GPUS    : $GPU_BITS"
echo "$PREFIX : RANK    : $MPI_RANK"
echo "$PREFIX : THREADS : $THREAD_NUM"

# if so requested, sleep for a bit
test -z "$ARG" || sleep $ARG

