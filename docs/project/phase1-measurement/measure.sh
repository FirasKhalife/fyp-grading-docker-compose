#!/bin/bash
# usage: measure.sh LABEL  -> idle (2 min) then light load (3 min)
SP="$(cd "$(dirname "$0")" && pwd)"; L=$1
echo "##### $L IDLE"; bash "$SP/sample.sh" "$L-idle" 20 4
bash "$SP/load.sh" 260 4; sleep 40
echo "##### $L LOAD (4 visitors)"; bash "$SP/sample.sh" "$L-load" 30 4
echo "##### load http codes per visitor"; bash "$SP/loadresult.sh"
free -m | head -2
