import plotly.graph_objects as go
from plotly.colors import DEFAULT_PLOTLY_COLORS

import dash
from dash import dcc
from dash import html
import dash_bootstrap_components as dbc


class Node:
    def __init__(self, name, color="black"):
        self.name = name
        self.color = color
        nodes.append(self)


class Link:
    def __init__(self, source, target, value):
        self.source = source
        # self.source_index = find_node_index(source.name, nodes)
        self.target = target
        # self.target_index = find_node_index(target.name, nodes)
        self.value = value
        self.color = self.source.color.replace("0.8", "0.4")


nodes = []

fusion_power = Node("Fusion power")
heating_system = Node("Heating System")
heating_losses = Node("Losses")
plasma = Node("Plasma")
neutrons = Node("Neutrons")
neutron_energy_multiplication = Node("Energy multiplication")
alphas = Node("Alphas")
fw = Node("First Wall")
blanket = Node("Blanket")
divertor = Node("Divertor")
elec_gen = Node("Electricity generator")
electricity = Node("Electricity")
output = Node("Net Electricity")
elec_gen_losses = Node("Losses")
pumping_losses = Node("Pumping")
magnets = Node("Magnets")


default_prms = {
    "Q_plasma": 50,
    "heating_power": 1,
    "neutrons_to_alpha": 4,
    "neutron_multiplication_factor": 1.3,
    "elec_generation_efficiency": 0.25,
    "alpha_in_fw_ratio": 0.9,
    "neutrons_in_bb_ratio": 0.9,
    "heating_efficiency": 0.3,
    "elec_to_pumps": 0.1,
    "elec_to_magnets": 0.1

}

def make_graph(prms=default_prms):
    Q_plasma = prms["Q_plasma"]

    heating_power = prms["heating_power"]
    heating_efficiency = prms["heating_efficiency"]
    fusion_power_value = heating_power*float(Q_plasma)
    neutrons_to_alpha_ratio = prms["neutrons_to_alpha"]
    neutrons_power_from_plasma = 1/(1 + 1/neutrons_to_alpha_ratio)*(fusion_power_value+ heating_power)
    alphas_power = 1/(1 + neutrons_to_alpha_ratio)*(fusion_power_value + heating_power)

    neutron_multiplication_factor = prms["neutron_multiplication_factor"]
    neutrons_power = neutrons_power_from_plasma

    neutrons_in_blanket_ratio = prms["neutrons_in_bb_ratio"]
    neutrons_in_div_ratio = 1 - neutrons_in_blanket_ratio

    alpha_in_fw_ratio = prms["alpha_in_fw_ratio"]
    alpha_in_div_ratio = 1 - alpha_in_fw_ratio

    fw_to_blanket_efficiency = 1

    blanket_power = alphas_power*alpha_in_fw_ratio*fw_to_blanket_efficiency + neutrons_power*neutrons_in_blanket_ratio*neutron_multiplication_factor
    divertor_power = alphas_power*alpha_in_div_ratio + neutrons_power*neutrons_in_div_ratio

    thermal_energy = blanket_power + divertor_power
    elec_gen_efficiency = prms["elec_generation_efficiency"]
    electricity_val = thermal_energy*elec_gen_efficiency

    elec_gen_losses_value = thermal_energy*(1-elec_gen_efficiency)
    elec_to_magnets_value = prms["elec_to_magnets"]*electricity_val
    elec_to_pumping_value = prms["elec_to_pumps"]*electricity_val
    heating_power_gross = heating_power/heating_efficiency

    net_electricity = electricity_val - heating_power_gross - elec_to_pumping_value - elec_to_magnets_value

    for i, node in enumerate(nodes):
        node.color = DEFAULT_PLOTLY_COLORS[i%len(DEFAULT_PLOTLY_COLORS)].replace(")", ", 0.8)").replace("rgb", "rgba")

    pumping_losses.color = electricity.color
    magnets.color = electricity.color
    elec_gen_losses.color = elec_gen.color
    neutron_energy_multiplication.color = neutrons.color

    links = [
        Link(fusion_power, plasma, fusion_power_value),
        Link(heating_system, heating_losses, heating_power_gross*(1 - heating_efficiency)),
        Link(heating_system, plasma, heating_power),
        Link(plasma, neutrons, neutrons_power_from_plasma),
        Link(plasma, alphas, alphas_power),
        Link(alphas, fw, alphas_power*alpha_in_fw_ratio),
        Link(alphas, divertor, alphas_power*alpha_in_div_ratio),
        Link(fw, blanket, alphas_power*alpha_in_fw_ratio*fw_to_blanket_efficiency),
        Link(neutrons, blanket, neutrons_power*neutrons_in_blanket_ratio),
        Link(neutron_energy_multiplication, blanket, neutrons_power*neutrons_in_blanket_ratio*(neutron_multiplication_factor-1)),
        Link(neutrons, divertor, neutrons_power*neutrons_in_div_ratio),
        Link(blanket, elec_gen, blanket_power),
        Link(divertor, elec_gen, divertor_power),
        Link(elec_gen, electricity, electricity_val),
        Link(elec_gen, elec_gen_losses, elec_gen_losses_value),
        Link(electricity, pumping_losses, elec_to_pumping_value),
        Link(electricity, magnets, elec_to_magnets_value),
        Link(electricity, output, net_electricity),
        Link(electricity, heating_system, heating_power_gross)
    ]

    sankey = go.Sankey(
        valuesuffix="MW",
        # arrangement="snap",
        node={
            "label": [node.name for node in nodes],
            'pad': 10,
            "color": [node.color for node in nodes],
            },
        link={
            "source": [nodes.index(link.source) for link in links],
            "target": [nodes.index(link.target) for link in links],
            "value": [link.value for link in links],
            "color": [link.color for link in links]
            })

    fig = go.Figure(sankey)

    # fig.show()
    return fig


app = dash.Dash(__name__)

server = app.server

graph1 = dcc.Graph(
        id='graph1',
        figure=make_graph(),
    )

Q_layout = html.Div([
    html.Div("Q_plasma"), dcc.Input(id='Q box', type='number', value=50, min=0),
    html.Div("Heating power (MW)"), dcc.Input(id='heating box', type='number', value=1, min=0),
    html.Div("E_neutrons/E_alphas"), dcc.Input(id='neutr to alpha ratio', type='number', value=4, min=0),
    html.Div("Energy multiplication factor"), dcc.Input(id='neutron mult box', type='number', value=1.2, min=1),
    html.Div("Electricity generation efficiency"), dcc.Input(id='generator efficiency box', type='number', value=0.25, min=0, max=1, step=0.01),
    html.Div("Alphas FW/div ratio"), dcc.Input(id='alphas FW/div ratio', type='number', value=0.9, min=0, max=1, step=0.1),
    html.Div("Neutrons blanket/div ratio"), dcc.Input(id='neutrons BB/div ratio', type='number', value=0.9, min=0, max=1, step=0.1),
    html.Div("Heating efficiency"), dcc.Input(id='heating efficiency', type='number', value=0.9, min=0.1, max=1, step=0.1),
    html.Div("P_magnets/P_elec"), dcc.Input(id='elec to magnets ratio', type='number', value=0.1, min=0, max=1, step=0.1),
    html.Div("P_pumps/P_elec"), dcc.Input(id='elec to pumps ratio', type='number', value=0.1, min=0, max=1, step=0.1),
    ]
)

github_button = html.Iframe(
        src="https://ghbtns.com/github-btn.html?user=remdelaportemathurin&repo=sankey_fusion&type=star&count=true&size=large",
        width="170",
        height="30",
        title="GitHub",
        style={"border": 0, "scrolling": "0"},
    )

layout = html.Div(children=[github_button, graph1, Q_layout])
app.layout = layout


@app.callback(
    dash.Output('graph1', 'figure'),
    dash.Input('Q box', 'value'),
    dash.Input('heating box', 'value'),
    dash.Input('neutr to alpha ratio', 'value'),
    dash.Input('neutron mult box', 'value'),
    dash.Input('generator efficiency box', 'value'),
    dash.Input('alphas FW/div ratio', 'value'),
    dash.Input('neutrons BB/div ratio', 'value'),
    dash.Input('heating efficiency', 'value'),
    dash.Input('elec to magnets ratio', 'value'),
    dash.Input('elec to pumps ratio', 'value'),
)
def update_graph(Q, heating, neutr_to_alpha, neutron_mult, elec_gen_efficiency, alpha_FW_to_div, neut_BB_to_div, heating_eff, elec_to_magnets, elec_to_pumps):
    prms = [
        float(Q),
        float(heating),
        float(neutr_to_alpha),
        float(neutron_mult),
        float(elec_gen_efficiency),
        float(alpha_FW_to_div),
        float(neut_BB_to_div),
        float(heating_eff),
        float(elec_to_magnets),
        float(elec_to_pumps),
    ]
    prms = {
        "Q_plasma": float(Q),
        "heating_power": float(heating),
        "neutrons_to_alpha": float(neutr_to_alpha),
        "neutron_multiplication_factor": float(neutron_mult),
        "elec_generation_efficiency": float(elec_gen_efficiency),
        "alpha_in_fw_ratio": float(alpha_FW_to_div),
        "neutrons_in_bb_ratio": float(neut_BB_to_div),
        "heating_efficiency": float(heating_eff),
        "elec_to_pumps": float(elec_to_pumps),
        "elec_to_magnets": float(elec_to_magnets)

    }
    return make_graph(prms)


if __name__ == "__main__":
    app.run_server(debug=True)
