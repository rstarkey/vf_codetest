#!/bin/bash
RUN_TIMES=10
I=0

while [[ ${I} -lt  ${RUN_TIMES} ]]; do
	echo "RUN $$:${I}"
	I=$((I+1))
	sleep 10
done
