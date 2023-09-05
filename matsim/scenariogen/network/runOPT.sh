#!/bin/bash --login
#$ -l h_rt=700000
#$ -j y
#$ -m a
#$ -o ./logfile/logfile_$JOB_NAME.log
#$ -cwd
#$ -pe mp 6
#$ -l mem_free=4G
#$ -l cpuflag_avx2=1
#$ -N network-opt

date
hostname

source venv/bin/activate
module add java/17

jar="matsim-[name]-SNAPSHOT.jar"
input="input/*"
network="network.xml.gz"
ft="network-ft.csv.gz"

# Find a free port
while
  port=$(shuf -n 1 -i 49152-65535)
  netstat -atun | grep -q "$port"
do
  continue
done

command="java -cp ${jar} org.matsim.application.prepare.network.opt.FreespeedOptServer ${input}
 --network ${network} --input-features ${ft} --port ${port}"

echo ""
echo "command is $command"
echo ""

$command &

echo "Waiting to launch on ${port}..."

while ! nc -z localhost "${port}"; do
  sleep 0.5
done

export PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION=python

python3.9 -u -m matsim.scenariogen network-opt-freespeed --port "${port}"