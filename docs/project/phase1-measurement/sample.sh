#!/bin/bash
# usage: sample.sh LABEL SAMPLES INTERVAL_S  -> writes stats-LABEL.csv and prints summary
L=$1; N=${2:-12}; I=${3:-5}; OUT="$(dirname "$0")/stats-$L.csv"; : > "$OUT"
for ((k=1;k<=N;k++)); do
  ids=$(docker ps -q --filter label=com.docker.compose.project=fyp-grading)
  docker stats --no-stream --format '{{.Name}},{{.MemUsage}},{{.CPUPerc}}' $ids | sed "s/^/$k,/" >> "$OUT"
  sleep "$I"
done
awk -F, '
function mib(s){ split(s,a," "); v=a[1]; if(v~/GiB/){sub("GiB","",v);return v*1024} if(v~/MiB/){sub("MiB","",v);return v+0} if(v~/kB|KiB/){sub("[kK]i?B","",v);return v/1024} sub("B","",v); return v/1048576 }
{ m=mib($3); c=$4; sub("%","",c); n[$2]++; sm[$2]+=m; if(m>mx[$2])mx[$2]=m; sc[$2]+=c; if(c+0>cx[$2])cx[$2]=c+0; tot[$1]+=m; tc[$1]+=c }
END { printf "%-22s %9s %9s %8s %8s\n","container","avgMiB","maxMiB","avgCPU%","maxCPU%";
  for(k in n) printf "%-22s %9.0f %9.0f %8.1f %8.1f\n",k,sm[k]/n[k],mx[k],sc[k]/n[k],cx[k] | "sort -k2 -nr";
  close("sort -k2 -nr"); s=0;M=0;cs=0;cM=0;j=0; for(t in tot){j++; s+=tot[t]; if(tot[t]>M)M=tot[t]; cs+=tc[t]; if(tc[t]>cM)cM=tc[t]}
  printf "TOTAL  containers=%d  mem avg=%.0f MiB max=%.0f MiB | cpu avg=%.1f%% max=%.1f%% (100%%=1 core)\n", length(n), s/j, M, cs/j, cM }' "$OUT"
