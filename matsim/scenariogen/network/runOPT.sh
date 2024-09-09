#!/bin/bash --login
#SBATCH --time=200:00:00
#SBATCH --partition=smp
#SBATCH --output=./logfile/logfile_%x-%j.log
#SBATCH --nodes=1                       # How many computing nodes do you need (for MATSim usually 1)
#SBATCH --ntasks=1                      # How many tasks should be run (For MATSim usually 1)
#SBATCH --cpus-per-task=6              # Number of CPUs per task (For MATSim usually 8 - 12)
#SBATCH --mem=12G                       # RAM for the job
#SBATCH --job-name=network-opt         # name of your run, will be displayed in the joblist
#SBATCH --constraint=cpuflag_avx2:1
#SBATCH --mail-type=END,FAIL

date
hostname

source venv/bin/activate
module add java/21

jar="matsim-[name]-SNAPSHOT.jar"
input="input/*"
model="org.matsim.prepare.network.Model"
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
 --network ${network} --input-features ${ft} --model ${model} --port ${port}"

echo ""
echo "command is $command"
echo ""

$command &

echo "Waiting to launch on ${port}..."

while ! nc -z localhost "${port}"; do
  sleep 0.5
done

export PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION=python

python -u -m matsim.scenariogen network-opt-freespeed --port "${port}"