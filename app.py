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


def make_graph(prms=[50, 1, 14.1/3.5, 1.2, 0.25, 0.9, 0.9, 0.9]):
    Q_plasma = prms[0]

    heating_power = prms[1]
    heating_efficiency = prms[7]
    fusion_power_value = heating_power*float(Q_plasma)
    neutrons_to_alpha_ratio = prms[2]
    neutrons_power_from_plasma = 1/(1 + 1/neutrons_to_alpha_ratio)*(fusion_power_value+ heating_power)
    alphas_power = 1/(1 + neutrons_to_alpha_ratio)*(fusion_power_value + heating_power)

    neutron_multiplication_factor = prms[3]
    neutrons_power = neutrons_power_from_plasma

    neutrons_in_blanket_ratio = prms[6]
    neutrons_in_div_ratio = 1 - neutrons_in_blanket_ratio

    alpha_in_fw_ratio = prms[5]
    alpha_in_div_ratio = 1 - alpha_in_fw_ratio

    fw_to_blanket_efficiency = 1

    blanket_power = alphas_power*alpha_in_fw_ratio*fw_to_blanket_efficiency + neutrons_power*neutrons_in_blanket_ratio*neutron_multiplication_factor
    divertor_power = alphas_power*alpha_in_div_ratio + neutrons_power*neutrons_in_div_ratio

    thermal_energy = blanket_power + divertor_power
    elec_gen_efficiency = prms[4]
    electricity_val = thermal_energy*elec_gen_efficiency

    elec_gen_losses_value = thermal_energy*(1-elec_gen_efficiency)
    elec_to_pumping_value = 0.1*electricity_val
    elec_to_magnets_value = 0.05*electricity_val
    net_electricity = electricity_val - heating_power/heating_efficiency - elec_to_pumping_value - elec_to_magnets_value

    for i, node in enumerate(nodes):
        node.color = DEFAULT_PLOTLY_COLORS[i%len(DEFAULT_PLOTLY_COLORS)].replace(")", ", 0.8)").replace("rgb", "rgba")

    pumping_losses.color = electricity.color
    magnets.color = electricity.color
    elec_gen_losses.color = elec_gen.color
    neutron_energy_multiplication.color = neutrons.color

    links = [
        Link(fusion_power, plasma, fusion_power_value),
        Link(heating_system, heating_losses, heating_power/heating_efficiency*(1 - heating_efficiency)),
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
        Link(electricity, heating_system, heating_power/heating_efficiency)
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
    html.Div("Q_plasma"), dcc.Input(id='Q box', type='text', value="50"),
    html.Div("Heating power (MW)"), dcc.Input(id='heating box', type='text', value="1"),
    html.Div("E_neutrons/E_alphas"), dcc.Input(id='neutr to alpha ratio', type='text', value="14.1/3.5"),
    html.Div("Energy multiplication factor"), dcc.Input(id='neutron mult box', type='text', value="1.2"),
    html.Div("Electricity generation efficiency"), dcc.Input(id='generator efficiency box', type='text', value="0.25"),
    html.Div("Alphas FW/div ratio"), dcc.Input(id='alphas FW/div ratio', type='text', value="0.9"),
    html.Div("Neutrons blanket/div ratio"), dcc.Input(id='neutrons BB/div ratio', type='text', value="0.9"),
    html.Div("Heating efficiency"), dcc.Input(id='heating efficiency', type='text', value="0.9"),
    # html.Button('Submit', id='submit-val'),
    ]
)


layout = html.Div(children=[graph1, Q_layout])
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
)
def update_graph(Q, heating, neutr_to_alpha, neutron_mult, elec_gen_efficiency, alpha_FW_to_div, neut_BB_to_div, heating_eff):
    prms = [
        float(Q),
        float(heating),
        eval(neutr_to_alpha),
        float(neutron_mult),
        float(elec_gen_efficiency),
        float(alpha_FW_to_div),
        float(neut_BB_to_div),
        float(heating_eff),
    ]
    return make_graph(prms)


if __name__ == "__main__":
    app.run_server(debug=True)
