# matsim-tools

Official tools for working with MATSim output files

MATSim is an open-source, multi-agent transportation simulation framework. Find out more about MATSim at <https://matsim.org>

## Using this library

We are just at the very early stages of building this library. The API will change, things will break, and there are certainly bugs. You probably shouldn't use this for anything.

- We have only tested this using Anaconda Python. Only Python 3.x is supported.
- Our primary goal is to make MATSim play nice with **pandas** and **geopandas**, for data analysis workflows.
- Currently only MATSIm network, event, and plans files are supported. Hopefully more will be coming soon.
- For Geopandas network support, you also need to install `geopandas` and `shapely`.

## Quickstart

1. Install using `pip install matsim-tools`.

2. In lieu of real documentation, here is some sample code to get you started. Good luck!

```python
import matsim
import pandas as pd
from collections import defaultdict
%matplotlib inline

# -----------------------------------
# 1. Read a MATSim network:
net = matsim.read_network('output_network.xml.gz')

net.nodes
# Dataframe output:
#           x        y node_id
# 0  -20000.0      0.0       1
# 1  -15000.0      0.0       2
# 2    -865.0   5925.0       3
# ...

net.links
# Dataframe output:
#      length  capacity  freespeed  ...  link_id from_node to_node
# 0   10000.0   36000.0      27.78  ...        1         1       2
# 1   10000.0    3600.0      27.78  ...        2         2       3
# 2   10000.0    3600.0      27.78  ...        3         2       4
# ...

geo = net.as_geo()  # combines links+nodes into a Geopandas dataframe with LINESTRINGs
geo.plot()    # try this in a notebook to see your network!

# ------------------------------------
# 2. Stream through a MATSim event file.

# The event_reader returns a python generator function, which you can then
# loop over without loading the entire events file in memory.
# In this example let's sum up all 'entered link' events to get link volumes.

events = event_reader('output_events.xml.gz', filter='entered link,left link')

link_counts = defaultdict(int) # defaultdict creates a blank dict entry on first reference

for event in events:
    if event['type'] == 'entered link':
        link_counts[event['link']] += 1

# convert our link_counts dict to a pandas dataframe,
# with 'link_id' column as the index and 'count' column with value:
link_counts = pd.DataFrame.from_dict(link_counts, orient='index', columns=['count']).rename_axis('link_id')

# attach counts to our Geopandas network from above
volumes = geo.merge(counts, on='link_id')
volumes.plot(column='count', figsize=(40,40))

# ------------------------------------
# 3. Stream through a MATSim plans file.

plans = plan_reader('output_plans.xml.gz', selectedPlansOnly = True)

for person, plan in plans:

    # do stuff with this plan, e.g.
    work_activities = filter(
        lambda n: n.tag == 'activity' and n.attrib['type'] = ='w',
        plan)

    print('person', person.attrib['id'], 'selected plan w/', len(list(work_activities)), 'work-act')
    activities.append(num_activities)

# person 1 selected plan w/ 2 work-act
# person 10 selected plan w/ 1 work-act
# person 100 selected plan w/ 1 work-act
# ...

```
