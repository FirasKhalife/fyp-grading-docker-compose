for c in $(docker ps -q --filter name=loadgen-); do docker exec $c sh -c 'sort /tmp/codes | uniq -c | tr "\n" " "'; echo; docker rm -f $c >/dev/null; done
