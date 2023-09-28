#!/bin/bash --login
#$ -l h_rt=700000
#$ -j y
#$ -m a
#$ -o ./logfile/logfile_$JOB_NAME.log
#$ -cwd
#$ -pe mp 6
#$ -l mem_free=4G
#$ -N network-train

date
hostname

source venv/bin/activate
module add java/17

ft="network-ft.csv.gz"
intersections="result_intersections_scenario-base.csv"
routes="result_routes_scenario-base.csv"
name="Scenario"
package="org.matsim.prepare.network"
output="gen_code"
type="default"

command="python -u -m matsim.scenariogen network-train-model
 --name ${name} --package ${package} --model-type ${type} --output ${output}
 --network-features ${ft} --input-intersections ${intersections} --input-routes ${routes}"

echo ""
echo "command is $command"
echo ""

export PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION=python

$command