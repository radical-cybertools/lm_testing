#!/bin/sh
# test the correct startup of mixed OpenMP / MPI / CPU / GPU tasks

# basic information
TID=$1
ARG=$2
PID=$$
NODE=$(hostname)

# get MPI rank
MPI_RANK=""
test -z "$MPI_RANK" && MPI_RANK="$ALPS_APP_PE"
test -z "$MPI_RANK" && MPI_RANK="$PMIX_RANK"
test -z "$MPI_RANK" && MPI_RANK="$PMI_RANK"

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

# same information about GPU pinning
# (assume we have no more GPUs than cores)
GPU_INFO=""
test -z "$GPU_INFO" && GPU_INFO="$CUDA_VISIBLE_DEVICES"
test -z "$GPU_INFO" && GPU_INFO="$GPU_DEVICE_ORDINAL"
GPU_INFO=$(echo " $GPU_INFO " | tr ',' ' ')

GPU_NBITS=$(echo $CPU_BITS | tr '1' '0' | wc -c)
GPU_BITS=''
n=1
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

# redirect output based on task ID and MPI rank
if test -z "$_REDIR"
then
    if ! test -z "$MPI_RANK"
    then
        TGT="$TID.$MPI_RANK"
    else
        TGT="$TID"
    fi
fi

# run js_task_info if available (summit)
js_task_info >"$TGT.info" 2>/dev/null

(
    echo "PID    : $PID"
    echo "NODE   : $NODE"
    echo "CPUS   : $CPU_BITS"
    echo "GPUS   : $GPU_BITS"
    echo "RANK   : $MPI_RANK"
    echo "THREADS: $THREAD_NUM"
) >"$TGT.out"

# if so requested, sleep for a bit
test -z "$ARG" || sleep $ARG



