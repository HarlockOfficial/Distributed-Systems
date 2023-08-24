import json
import os
from typing import Dict, Tuple, Any, List

os.environ['SSHELL_PATH'] = '/home/administrator/Desktop/sibilla/shell/build/install/sshell'


def run_simulation(graph_input_file_name: str, file_name: str, deadline: float, system_name: str,
                   delta: float = 1.0, replica_amount: int = 1, seed: int = None, measures: list = None) \
        -> Tuple[int, Any]:
    import sibilla
    runtime = sibilla.SibillaRuntime()
    runtime.load_module('population')
    runtime.load_from_file(file_name)
    runtime.set_configuration(system_name)

    if measures is not None:
        if len(measures) > 0:
            runtime.add_measures(*measures)

    runtime.set_deadline(deadline)
    runtime.set_dt(delta)

    if replica_amount > 1:
        runtime.set_replica(replica_amount)

    if seed is None:
        seed = runtime.get_seed()
    else:
        runtime.set_seed(seed)

    simulation_results = runtime.simulate('test')

    # use matplotlib, default plot crashes if more than 10 measures are set
    # simulation_results.plot()
    # simulation_results.plot_detailed()
    # simulation_results.plot(show_sd=False)
    results_save_path = 'results/' + graph_input_file_name + '/' + str(seed) + '/' + str(replica_amount) + '/' + system_name
    if not os.path.exists(results_save_path):
        os.makedirs(results_save_path)

    runtime.save(results_save_path, prefix='', postfix='')
    runtime.clear()
    return seed, simulation_results


def read_communication_graph(path_to_latex_tkiz_graph: str) -> Tuple[list, list]:
    """
    Generate a communication graph from a tkiz graph.
    Assuming that the graph is written as it was latex code.
    therefore, the file is structured as follows:
    % comment
    \begin{tikzpicture}[options]
        \node (node_name) [node_type] {node_label};
        ...
        \node (node_name) [node_type] {node_label};

        \path [options]
            (node_name) edge [edge_type] {edge_label} (node_name)
            (node_name) edge [edge_type] {edge_label} (node_name)
            ...
            (node_name) edge [edge_type] {edge_label} (node_name);
    \end{tikzpicture}

    Note: for this implementation I'm considering the node_name to be the identifier of the node in the graph.
    """
    nodes = list()
    edges = list()
    with open(path_to_latex_tkiz_graph, 'r') as f:
        lines = f.readlines()
        lines = [line.strip() for line in lines if line.strip() != '']
        lines = [line for line in lines if line[0] != '%']
        for line in lines:
            if line.startswith('\\node'):
                node_id = line.split('(')[1].split(')')[0]
                nodes.append(node_id)
            elif ') edge ' in line:
                edge_start = line.split('(')[1].split(')')[0]
                edge_end = line.split('(')[2].split(')')[0]
                edges.append((edge_start, edge_end))
    return nodes, edges


def generate_system_string_and_measures(nodes: list, edges: list, system_name: str) -> Tuple[str, List[str]]:
    """
    Generate the system string from the nodes and edges.
    The system string is in the format:
    system <system_name> = N[i for i in [0, <len(nodes)>]] | C[<edge_id_1[0]>, <edge_id_1[1]>] |
                            C[<edge_id_2[0]>, <edge_id_2[1]>] | ... | C[<edge_id_m[0]>, <edge_id_m[1]>];

    Also generate two measures for each node and edge:
    - %N[<node_id>]: the percentage of nodes in the population
    - #N[<node_id>]: the number of nodes in the population
    - %C[<edge_id_1[0]>, <edge_id_1[1]]: the percentage of edges in the population
    - #C[<edge_id_1[0]>, <edge_id_1[1]]: the number of edges in the population
    - %L[<node_id>]: the percentage of nodes that are leaders
    - #L[<node_id>]: the number of nodes that are leaders
    - %F[<node_id_1>, <node_id_2>]: the percentage of nodes that are followers
    - #F[<node_id_1>, <node_id_2>]: the number of nodes that are followers
    """
    output = 'system ' + system_name + ' = '
    measures = []
    # Note: here all nodes are add separately in the form "N[i] | ..." instead of "N[i for i in [0, len(nodes)]]"
    #      this is because some nodes might not exist in the graph and some IDs might be missing
    #      therefore is not guaranteed that the nodes are in order and numbered from 0 to len(nodes)
    for i in nodes:
        # not using the contract for N[i for i in [0, len(nodes)]] because some nodes might not exist
        output += 'N[' + str(i) + '] | '
        measures.append('%N[' + str(i) + ']')
        measures.append('#N[' + str(i) + ']')
        measures.append('%L[' + str(i) + ']')
        measures.append('#L[' + str(i) + ']')

    for edge in edges:
        output += 'C[' + str(edge[0]) + ', ' + str(edge[1]) + '] | '

    output = output[:-3] + ';'

    for i in nodes:
        for j in nodes:
            if i != j:
                measures.append('%F[' + str(i) + ', ' + str(j) + ']')
                measures.append('#F[' + str(i) + ', ' + str(j) + ']')
            measures.append('%C[' + str(i) + ', ' + str(j) + ']')
            measures.append('#C[' + str(i) + ', ' + str(j) + ']')
            measures.append('%C[' + str(j) + ', ' + str(i) + ']')
            measures.append('#C[' + str(j) + ', ' + str(i) + ']')

    return output, measures


def apply_system_string_to_simulation_file(system_string: str, simulation_file: str) -> str:
    with open(simulation_file, 'r') as f:
        lines = f.readlines()
    lines = [line.strip() for line in lines]
    lines = [line for line in lines if line != '']
    lines = [line for line in lines if not line.startswith('/*')]
    lines = [line for line in lines if not line.startswith('*/')]
    lines = [line for line in lines if not line.startswith('*')]

    # Remove the system string
    lines = [line for line in lines if not line.startswith('system')]

    # Add the system string
    lines.append(system_string)

    new_filename = simulation_file.split('.')[0] + '_new.' + simulation_file.split('.')[1]

    with open(new_filename, 'w') as f:
        for line in lines:
            f.write(line + '\n')

    return new_filename


def apply_parameters_to_simulation_file(new_filename: str, parameters: Dict[str, float] = None) -> None:
    if parameters is None:
        return
    with open(new_filename, 'r') as f:
        lines = f.readlines()
    out_lines = list()
    for line in lines:
        if 'param' in line:
            param_name = line.split('param')[1].split(';')[0].strip()
            if '=' in param_name:
                param_name = param_name.split('=')[0].strip()
            if param_name in parameters:
                line = 'param ' + param_name + ' = ' + str(parameters[param_name]) + ';\n'
        out_lines.append(line)

    with open(new_filename, 'w') as f:
        for line in out_lines:
            f.write(line)


def main(communication_graph_file: str, simulation_file: str, deadline: float,
         delta: float = 1.0, replica_amount: int = 1, seed: int = None,
         parameters: Dict[str, float] = None):
    """
    Main function.
    Parameter list:
    - communication_graph_file: the path to the communication graph file
    - simulation_file: the path to the original simulation file
    - deadline: the deadline of the simulation
    - delta: the delta of the simulation
    - replica_amount: the amount of replicas to run
    - seed: the seed of the simulation
    - parameters: a dictionary containing the parameters of the simulation
    """
    # Generate the system string
    nodes, edges = read_communication_graph(communication_graph_file)
    import uuid
    system_name = uuid.uuid4().hex
    if system_name[0].isdigit():
        system_name = 's' + system_name[1:]
    system_string, measures = generate_system_string_and_measures(nodes, edges, system_name)
    new_filename = apply_system_string_to_simulation_file(system_string, simulation_file)
    apply_parameters_to_simulation_file(new_filename, parameters)

    graph_input_file_name = communication_graph_file.split('/')[1].split('.')[0]

    # Run the simulation
    seed, simulation_results = run_simulation(graph_input_file_name, new_filename, deadline, system_name, delta,
                                              replica_amount, seed, measures)
    print(seed)


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Run a simulation with a communication graph.')
    parser.add_argument('communication_graph_file', type=str, help='The path to the communication graph file.')
    parser.add_argument('simulation_file', type=str, help='The path to the simulation file.')
    parser.add_argument('deadline', type=float, help='The deadline of the simulation.')
    parser.add_argument('--delta', type=float, default=1.0, help='The delta of the simulation.')
    parser.add_argument('--replica_amount', type=int, default=1, help='The amount of replicas to run.')
    parser.add_argument('--seed', type=int, default=None, help='The seed of the simulation.')
    parser.add_argument('--parameters', type=json.loads, default=None,
                        help='A dictionary containing the parameters of the simulation.')
    args = parser.parse_args()
    main(args.communication_graph_file, args.simulation_file, args.deadline, args.delta, args.replica_amount,
         args.seed, args.parameters)
