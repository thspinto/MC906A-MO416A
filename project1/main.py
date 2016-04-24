#!/usr/bin/env python3
#
# Copyright 2016 (C) Thiago Pinto.
#
# This software may be modified and distributed under the terms
# of the MIT license.  See the LICENSE file for details.

"""
Genetic algorithm that attributes stories to the next sprint of the development
teams otimizing the project's cost and aggregated value.
"""
__author__ = "Thiago Pinto"

import sys
import csv
import json
from story_selector import StorySelector

def main():
    """
    Import scrum data, algorithm configuration and execute algorithm.

    Input:
        @arg backlog: backlog in CSV
        @arg team_specs: team specifications in CSV
        @arg configs: algorithm configurations

    Output:

    """

    check_args()
    backlog = parse_csv(sys.argv[1])
    team_specs = parse_csv(sys.argv[2])
    configs = parse_json(sys.argv[3])

    story_selector = StorySelector(configs)
    story_selector.generate_random_solution(backlog, team_specs)
    #for config in configs:
        #execute algorithm with configuration


def parse_json(file_name):
    """
    Parse JSON file

    @param file_name: the name of the file to be read and parsed
    """
    with open(file_name) as jfile:
        return json.loads(jfile.read())


def parse_csv(file_name):
    """
    Parses the CSV file ignoring the header and returns a dictionary {id: data}.

    @param file_name: the name of the file to be read and parsed
    """
    data = {}
    with open(file_name, encoding='utf-8') as csvfile:
        reader = csv.reader(csvfile, delimiter=',', quotechar='"')
        header = next(reader)
        for row in reader:
            data[row[0]] = {header[i]:row[i] for i in range(1,len(header))}

    convert_numbers(data)
    return data

def convert_numbers(parsed_data):
    """
    Convert number fields to floar in parsed_data

    @param parsed_data: data parsed_data from csv_file
    """
    expected_number_filds = ['efficiency', 'cost', 'available_time', 'priority','time']
    for value in parsed_data.values():
        for key in expected_number_filds:
            if key in value:
                value[key] = float(value[key])


def check_args():
    """
    Check command line arguments and print help text

    Expected call:
        ./main.py <backlog.csv> <teams.csv> <alg_config.json>

    File format example can be seen in /data directory
    """
    if len(sys.argv) != 4:
        print("Expected arguments: ./main.py <backlog.csv> <teams.csv> <alg_config.json>")
        exit(-1)


if __name__ == '__main__':
    sys.exit(main())
