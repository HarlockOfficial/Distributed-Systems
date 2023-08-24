"""
This file is used to plot the results of the simulation.
uses as parameters the root directory containing all the simulation results.
The specified folder contains a list of csv files.
The file name is as follows:
    <measure_name_to_take_into_account>.csv
    Note: the simulation seed is not meaningful for the means of the script.

Each file contains exactly 4 columns:
    - the first column is the time tick of the simulation
    - the second column is the average value of the measure at the time tick
    - the third column is the standard deviation of the measure at the time tick
    - the fourth column is the confidence interval of the measure at the time tick

    Note: of all the values is considered the mean among all the simulation replicas
    Note: the files don't have an header row

Is necessary to plot two types of diagrams:
    - one for each measure
    - one containing all the measures
"""


def add_headers_to_file(file: str) -> None:
    """
    Add the headers to the specified file.
    :param file: the file to which add the headers.
    """
    import os
    if not os.path.isfile(file):
        return
    with open(file, 'r') as f:
        lines = f.readlines()
    if len(lines) == 0:
        return
    if lines[0].startswith('time'):
        return
    with open(file, 'w') as f:
        f.write('time,mean,standard_deviation,confidence_interval\n')
        for line in lines:
            f.write(line)


def load_all_results(simulation_results_folder: str) -> dict:
    """
    Load all the results from the simulation results folder.
    :param simulation_results_folder: the path to the simulation results folder.
    :return: a dictionary containing all the results.
    """
    import os
    import pandas as pd
    results = dict()
    for file in os.listdir(simulation_results_folder):
        add_headers_to_file(simulation_results_folder + '/' + file)
        if file.endswith('.csv'):
            measure_name = file.split('.')[0]
            results[measure_name] = pd.read_csv(simulation_results_folder + '/' + file, sep=',')
    return results


def main(simulation_results_folder: str):
    results = load_all_results(simulation_results_folder)
    import matplotlib.pyplot as plt
    # plot one figure for each measure
    for measure_name, measure_results in results.items():
        plt.figure()
        plt.title(measure_name)
        plt.xlabel('Time (s)')
        plt.ylabel('Value')
        plt.grid()
        plt.errorbar(measure_results['time'], measure_results['mean'], yerr=measure_results['confidence_interval'], label=measure_name)
        plt.legend()
        plt.savefig(simulation_results_folder + '/plot/' + measure_name + '.png')
        plt.close()

    # plot one figure containing all the measures
    plt.figure()
    plt.title('All measures')
    plt.xlabel('Time (s)')
    plt.ylabel('Value')
    plt.grid()
    for measure_name, measure_results in results.items():
        plt.errorbar(measure_results['time'], measure_results['mean'], yerr=measure_results['confidence_interval'],
                     label=measure_name)
    plt.legend()
    plt.savefig(simulation_results_folder + '/plot/all_measures.png')
    plt.close()

    # plot one figure containing all the measures, divided by type
    all_measures_name = list(results.keys())
    all_measures_name.sort()
    group_of_measures = list()
    for measure_name in all_measures_name:
        if measure_name[:2] not in group_of_measures:
            group_of_measures.append(measure_name[:2])

    for group in group_of_measures:
        plt.figure()
        plt.title('All measures - ' + group)
        plt.xlabel('Time (s)')
        plt.ylabel('Value')
        plt.grid()
        for measure_name, measure_results in results.items():
            if measure_name.startswith(group):
                plt.errorbar(measure_results['time'], measure_results['mean'], yerr=measure_results['confidence_interval'],
                             label=measure_name)
        plt.legend()
        plt.savefig(simulation_results_folder + '/plot/all_measures_' + group + '.png')
        plt.close()


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Plot the results of the simulation.')
    parser.add_argument('simulation_results_folder', type=str, help='The path to the simulation results folder.')
    args = parser.parse_args()

    # remove all png in folder
    #import os
    #for file in os.listdir(args.simulation_results_folder):
    #    if file.endswith('.png'):
    #        os.remove(args.simulation_results_folder + '/' + file)

    # remove eventual trailing slash
    if args.simulation_results_folder.endswith('/'):
        args.simulation_results_folder = args.simulation_results_folder[:-1]

    # create directory for plots
    import os
    if not os.path.exists(args.simulation_results_folder + '/plot'):
        os.makedirs(args.simulation_results_folder + '/plot')

    main(args.simulation_results_folder)
