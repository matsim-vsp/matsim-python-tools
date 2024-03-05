"""
Plan Inheritance Record Inspector

Analyze the evolution of plans of a single agent or compare different agents side by side.
"""

# Import packages
from dash import Dash, html, dash_table, dcc, callback, Output, Input, ctx
import pandas as pd
import plotly.express as px
import dash_cytoscape as cyto # graph plotting
import dash_bootstrap_components as dbc # column formatting and stuff
import argparse
import io
import sys

# https://dash.plotly.com/cytoscape/layout
# Load extra layouts - time consuming
cyto.load_extra_layouts()
# https://github.com/cytoscape/cytoscape.js-dagre
# https://github.com/cytoscape/cytoscape.js-klay

# Process command line arguments
parser = argparse.ArgumentParser(prog="piri", description="Analyze the evolution of plans of a single agent or compare different agents side by side.")

if "piri" in sys.argv:
    parser.add_argument("cmd", help="Hidden argument to consume the 'piri' subcommand")

parser.add_argument("inputfile", help="Full path to the file containing the plan inheritance records, e.g. path/to/matsim/output/planInheritanceRecords.csv.gz")
args = parser.parse_args()

# Read and PreProcess data
pir = pd.read_csv(args.inputfile, sep='\t')
pir['mutatedBy'] = pir['mutatedBy'].str.replace('_', ' ', regex=False)
pir['iterationsSelected'] = pir['iterationsSelected'].str.replace('[', '', regex=False).str.replace(']', '',
                                                                                                    regex=False)
defaultagentId = pir['agentId'].unique()[0]
pir['nodeClasses'] = pir.apply(
    lambda row: "initial" if row['ancestorId'] == "NONE" else "final" if row['iterationRemoved'] == -1 else "regular",
    axis=1)

# Initialize the app
app = Dash(__name__,
    external_stylesheets=[dbc.themes.LUX] # required for column-based layouts
    )

nodes = []
edges = []

def get_graph_style():
   return [
        {
            'selector': 'node', # default node layout
            'style': {
                'label': 'data(label)',
                'text-rotation': '-90deg',
                'text-halign': 'center', # left, center, right
                'text-valign': 'center', # top, center, bottom
                'background-color': 'white',
                'background-opacity': 0.0,
                'height': '80%',
                'width': '20%'
                }
            },
        {
            'selector': '.legend', # layout for nodes tagged as legend
            'style': {
                'label': 'data(label)',
                'text-rotation': '0deg',
                'text-halign': 'center', # left, center, right
                'text-valign': 'center', # top, center, bottom
                'background-color': 'white',
                'background-opacity': 0.0,
                'height': '80%',
                'width': '20%'
                }
            },
        {
            'selector': '.initial', # layout for nodes tagged as initial plan
            'style': {
                'text-halign': 'center', # left, center, right
                'text-valign': 'center', # top, center, bottom
                'background-color': 'orange',
                'background-opacity': 0.2,
                'line-color': 'red',
                'shape': 'round-tag', # vee
                'height': '20%',
                'width': '20%'
                }
            },
        {
            'selector': '.final', # layout for nodes tagged as plans of the final choice-set
            'style': {
                'text-halign': 'center', # left, center, right
                'text-valign': 'center', # top, center, bottom
                'background-color': 'darkgreen',
                'background-opacity': 0.2,
                'line-color': 'red',
                'shape': 'round diamond',
                'height': '20%',
                'width': '20%'
                }
            },
       {
            'selector': 'edge', # default layout for edges
            'style': {
                #'label': 'whatever',
                'curve-style': 'straight',
                'target-arrow-color': 'dodgerblue',
                'target-arrow-shape': 'vee',
                'line-color': 'dodgerblue',
                'target-endpoint': '-90deg',
                'source-endpoint': '90deg'
                }
            },
        {
            'selector': '.long', # layout for edges spanning more than one iteration - used in the overview graph
            'style': {
                # The default curve style does not work with certain arrows
                'curve-style': 'unbundled-bezier',
                'curved': "true",
                'control-point-distances': (-30, -30),
                'control-point-weights': (0.1, 0.6),                
                'target-endpoint': '-90deg',
                'source-endpoint': '90deg'
                }
            }
        ]

# App layout
tab1_content = dbc.Container([

    dbc.Row([
        dcc.Dropdown(pir['agentId'].unique(), defaultagentId, clearable=False, placeholder="Select agent id", id='agentid-dropdown'),
        ]),

    dbc.Row([
        dash_table.DataTable(data=[],
            page_size=20, editable=False,
            style_data={
                'whiteSpace': 'normal',
                'height': 'auto',
                 },
            style_header={
                'textAlign': 'left',
                },
            style_cell={
                'overflow': 'hidden',
                'textOverflow': 'ellipsis',
                'textAlign': 'right',
                },
            style_data_conditional=[],
            tooltip_data=[],
            tooltip_duration=None,
            sort_action='native',
            sort_by=[{'column_id': 'iterationCreated', 'direction': 'asc'}],
            columns=[
                #{"name": "Agent", "id": "agentId"},
                {"name": ["Id", "Plan"], "id": "planId"},
                {"name": ["Id", "Ancestor"], "id": "ancestorId"},
                {"name": ["Id", "Strategies"], "id": "mutatedBy"},
                {"name": ["Iteration", "Created"], "id": "iterationCreated"},
                {"name": ["Iteration", "Removed"], "id": "iterationRemoved"},
                {"name": ["Iteration", "Selected"], "id": "iterationsSelected"}
                ],
            merge_duplicate_headers=True,
            id='agentid-table'),
            ]),

    html.Hr(),
    
    dbc.Row([
        dbc.Col([
            html.P('Overview - Each plan one node', className="card-text"),
            cyto.Cytoscape(
                id='cytoscape-simple', # plots each plan only once
                layout={
                    'name': 'dagre',
                    'rankDir': 'LR',
                    },
                style={'width': '100%', 'height': '600px'},
                elements=[],
                stylesheet=get_graph_style()
                ),
            ], width="2"),
        
        dbc.Col([
            html.P('Expanded view - Selected plan for each iteration', className="card-text"),
            cyto.Cytoscape(
                id='cytoscape-detail', # plots the selected plan of each iteration
                layout={
                    'name': 'dagre',
                    'rankDir': 'LR',
                    #'nodeSep': '20',
                    'rankSep': '10',
                    },
                style={'width': '100%', 'height': '600px'},
                elements=[],
                stylesheet=get_graph_style()
                ),
            ], width="10"),
        ]),
    ], fluid=True)

tab2_content = dbc.Card(
    dbc.CardBody(
        [
            html.P("Plots the selected plan of each iteration for the first n agents.", className="card-text"),
            #html.Div(className='row', children='Expanded view - Selected plan for each iteration'),
            dcc.Input(id='number-of-agents', type='number', min=1, max=1000, step=1, debounce=True), dbc.Button("Click here to load", id='large-viz-load-button', color="blue", n_clicks=0),
            cyto.Cytoscape(
                id='cytoscape-large',
                layout={
                    'name': 'preset'
                    },
                style={'width': '100%', 'height': '1000px'},
                elements=[],
                stylesheet=get_graph_style()
                ),
            ]),
        )

# The actual app layout
app.layout = dbc.Tabs(
    [
        dbc.Tab(
            'Allows to inspect inspect the plans of a single agent or gives an overview of the first n agents.', label="Plan Inheritance Record Inspector", disabled=True
            ),
        dbc.Tab(tab1_content, label="Single Agent Analysis"),
        dbc.Tab(tab2_content, label="Top N Overview")
    ]
)

@callback(
    Output('cytoscape-large', 'elements'),
    #Input('large-viz-load-button', 'n_clicks'),
    Input('number-of-agents', 'value'),
    prevent_initial_call=True
)
def on_load_button_clicked(value):
    # activates once the input field looses the focus - either by tabbing out or by "clicking" the button
    agent_ids = pir['agentId'].unique()

    max_iteration = 0
    expanded_list = []
    agent_number = 0
    for agent_id in agent_ids:
        filtered_pir = pir.loc[pir['agentId'] == agent_id]
        filtered_pir = filtered_pir.reset_index()  # make sure indexes pair with number of rows

        agent_number += 1

        if agent_number > value:
            break # limit the number of agents
        
        for index, row in filtered_pir.iterrows(): # may work for small data frames
            
            ancestor = row['ancestorId']
           
            if ancestor != "NONE":
                ancestor_suffix = ""
                created = row['iterationCreated']
                ancestor_row = filtered_pir.loc[filtered_pir['planId'] == ancestor]
                        
                # it's always only one single entry since the planId is globally unique per definition
                for ancestor_selected in ancestor_row['iterationsSelected'].iloc[0].split(','):
                    if int(ancestor_selected) < created:
                        ancestor_suffix = ancestor_selected
        
                ancestor = row['ancestorId'] + "_" + ancestor_suffix
            
            for selected in row['iterationsSelected'].split(','):
                if max_iteration < int(selected):
                    max_iteration = int(selected)
                
                dict_expanded = {
                    'agentId': agent_id,
                    'agentNumber': agent_number,
                    'iterationNumber': int(selected),
                    'origPlanId': row['planId'],
                    'planId': row['planId'] + "_" + selected,
                    'ancestorId': ancestor,
                    'label': row['planId'],
                    'nodeClasses': row['nodeClasses']}
                expanded_list.append(dict_expanded) # one entry per iteration selected
                ancestor = row.planId + "_" + selected
        
    expanded_pir = pd.DataFrame(expanded_list)
    # add info about whether this edge should have a long bezier-like curve or a regular straight one
    expanded_pir['edgeClasses'] = expanded_pir.apply(lambda row: "short" if row['ancestorId'] == "NONE" else "short" if (row['iterationNumber'] - int(row['ancestorId'].split("_")[1]) == 1) and (row['origPlanId'] == row['ancestorId'].split("_")[0]) else "long", axis=1)
   
    nodes_detail = [
        {'data': {'id': id, 'label': label, 'origPlanId': origPlanId}, 'position': {'x': 40 * x, 'y': 75 * y}, 'classes': nodeClasses} for id, label, origPlanId, x, y, nodeClasses in zip(expanded_pir.planId, expanded_pir.label, expanded_pir.origPlanId, expanded_pir.iterationNumber, expanded_pir.agentNumber, expanded_pir.nodeClasses)
        ]
   
    edges_detail = [
        {'data': {'source': source, 'target': target}, 'classes': edgeClasses} for source, target, edgeClasses in zip(expanded_pir.ancestorId, expanded_pir.planId, expanded_pir.edgeClasses)
        ]
    edges_detail = [x for x in edges_detail if not "NONE" in x.get("data").get("source")]  

    # add nodes as legend 
    for agent_entry in expanded_list:
        nodes_detail.append({'data': {'id': agent_entry["agentId"], 'label': agent_entry["agentId"], 'origPlanId': agent_entry["agentId"]}, 'position': {'x': -50, 'y': 75 * agent_entry["agentNumber"]}, 'classes': "legend"})

    for iteration in range(max_iteration + 1):
        nodes_detail.append({'data': {'id': str(iteration), 'label': str(iteration), 'origPlanId': str(iteration)}, 'position': {'x': 40 * iteration, 'y': 0}, 'classes': "legend"})
     
    return nodes_detail + edges_detail
    
@callback(
    [Output('cytoscape-simple', 'elements'), Output('cytoscape-detail', 'elements'), Output('agentid-table', 'data'), Output('agentid-table', 'tooltip_data')],
    [Input('agentid-dropdown', 'value')]
    )
def filter_single_agent_analysis_graphs_and_table_data(selectedAgent):
    # activates once an agent id is selected
    filtered_pir = pir.loc[pir['agentId'] == selectedAgent]
    filtered_pir = filtered_pir.reset_index()  # make sure indexes pair with number of rows
   
    nodes = [
        {'data': {'id': id, 'label': label}, 'classes': nodeClasses} for id, label, nodeClasses in zip(filtered_pir.planId, filtered_pir.planId, filtered_pir.nodeClasses)
        ]
   
    edges = [
        {'data': {'source': source, 'target': target}} for source, target in zip(filtered_pir.ancestorId, filtered_pir.planId)
        ]
    edges = [x for x in edges if not "NONE" in x.get("data").get("source")]

    expanded_list = []
    for index, row in filtered_pir.iterrows(): # may work for small data frames
        
        ancestor = row['ancestorId']
       
        if ancestor != "NONE":
            ancestor_suffix = ""
            created = row['iterationCreated']
            ancestor_row = filtered_pir.loc[filtered_pir['planId'] == ancestor]
                    
            # it's always only one single entry since the planId is globally unique per definition
            for ancestor_selected in ancestor_row['iterationsSelected'].iloc[0].split(','):
                if int(ancestor_selected) < created:
                    ancestor_suffix = ancestor_selected

            ancestor = row['ancestorId'] + "_" + ancestor_suffix
        
        for selected in row['iterationsSelected'].split(','):
            dict_expanded = {
                'origPlanId': row['planId'],
                'planId': row['planId'] + "_" + selected,
                'ancestorId': ancestor,
                'label': selected + "-" + row['planId'],
                'nodeClasses': row['nodeClasses']
                }
            expanded_list.append(dict_expanded)
            ancestor = row.planId + "_" + selected

    expanded_pir = pd.DataFrame(expanded_list)

    nodes_detail = [
        {'data': {'id': id, 'label': label, 'origPlanId' : origPlanId}, 'classes': nodeClasses} for id, label, origPlanId, nodeClasses in zip(expanded_pir.planId, expanded_pir.label, expanded_pir.origPlanId, expanded_pir.nodeClasses)
        ]
   
    edges_detail = [
        {'data': {'source': source, 'target': target}} for source, target in zip(expanded_pir.ancestorId, expanded_pir.planId)
        ]
    edges_detail = [x for x in edges_detail if not "NONE" in x.get("data").get("source")]

    data = filtered_pir.to_dict('records') # sets the data of the table
    
    tooltip_data = [ # sets the tooltip for each cell
        {
            column: {'value': str(value), 'type': 'markdown'}
            for column, value in row.items()
        } for row in data
        ]
    
    return nodes + edges, nodes_detail + edges_detail, data, tooltip_data

@callback(
    Output('agentid-table', 'style_data_conditional'),
    [Input('cytoscape-simple', 'mouseoverNodeData'),
     Input('cytoscape-detail', 'mouseoverNodeData')],
     prevent_initial_call=True
    )
def mouse_over_node_data(data_simple, data_detail):
    # activates once the user hovers over a node and highlights the corresponding row
    triggered_id = ctx.triggered_id
    
    search_value = ""

    if triggered_id == 'cytoscape-simple':
         search_value = data_simple['id']
    elif triggered_id == 'cytoscape-detail':
         search_value = data_detail['origPlanId']

    return [{
        'if': {
            'filter_query': '{planId} eq ' + search_value
            },
        'backgroundColor': 'dodgerblue',
        'color': 'white'
        }]

# Run the app
if __name__ == '__main__':
    app.run(debug=False)
