import plotly.graph_objects as go
from plotly.colors import DEFAULT_PLOTLY_COLORS

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


def make_graph(prms=[50, 0.18, 1.2, 0.25]):
    # Q_plasma = 50
    Q_plasma = prms[0]

    # heating_power = 0.18
    heating_power = prms[1]
    heating_efficiency = 0.9
    fusion_power_value = heating_power*float(Q_plasma)
    neutrons_to_alpha_ratio = 2/0.5
    neutrons_power_from_plasma = 1/(1 + 1/neutrons_to_alpha_ratio)*(fusion_power_value+ heating_power)
    alphas_power = 1/(1 + neutrons_to_alpha_ratio)*(fusion_power_value + heating_power)

    neutron_multiplication_factor = prms[2]
    neutrons_power = neutrons_power_from_plasma

    neutrons_in_blanket_ratio = 0.9
    neutrons_in_div_ratio = 0.1

    alpha_in_fw_ratio = 0.9
    alpha_in_div_ratio = 0.1

    fw_to_blanket_efficiency = 1

    blanket_power = alphas_power*alpha_in_fw_ratio*fw_to_blanket_efficiency + neutrons_power*neutrons_in_blanket_ratio*neutron_multiplication_factor
    divertor_power = alphas_power*alpha_in_div_ratio + neutrons_power*neutrons_in_div_ratio

    thermal_energy = blanket_power + divertor_power
    elec_gen_efficiency = prms[3]
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

    fig = go.Figure(go.Sankey(
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
    )

    # fig.show()
    return fig


# import plotly.express as px

# fig.write_html("my_reactor_sankey.html")

import dash
from dash import dcc
from dash import html
import dash_bootstrap_components as dbc

app = dash.Dash(__name__)

server = app.server

graph1 = dcc.Graph(
        id='graph1',
        figure=make_graph(),
        className="six columns"
    )

Q_layout = html.Div([
    html.Div("Q_plasma"), dcc.Input(id='Q box', type='text', value="50"),
    html.Div("Heating power"), dcc.Input(id='heating box', type='text', value="1"),
    html.Div("Energy multiplication"), dcc.Input(id='neutron mult box', type='text', value="1.2"),
    html.Div("Electricity generation efficiency"), dcc.Input(id='generator efficiency box', type='text', value="0.25"),
    html.Button('Submit', id='submit-val'),
    ]
)


layout = html.Div(children=[graph1, Q_layout])
app.layout = layout


@app.callback(
    dash.Output('graph1', 'figure'),
    dash.Input('submit-val', 'n_clicks'),
    dash.State('Q box', 'value'),
    dash.State('heating box', 'value'),
    dash.State('neutron mult box', 'value'),
    dash.State('generator efficiency box', 'value'),
)
def update_graph(n_clicks, Q, heating, neutron_mult, elec_gen_efficiency):
    prms = [
        float(Q),
        float(heating),
        float(neutron_mult),
        float(elec_gen_efficiency)
    ]
    return make_graph(prms)


if __name__ == "__main__":
    app.run_server(debug=True)
