# Copyright 2016 (C) Thiago Pinto.
#
# This software may be modified and distributed under the terms
# of the MIT license.  See the LICENSE file for details.

__author__ = "Thiago Pinto"

import random
from operator import itemgetter


class StorySelector:
    """
    Genetic algorithm implementation

    The algorithm consideres the following factors:
        - story priority;
        - story size in sprint points;
        - teams implementation speed in story points per hour;
        - story dependency (with oother stories)
        - team cost (in $ per hour)
    """

    def __init__(self, config,  backlog, teams):
        """
        Initialize global data structures

        @param config: algorithm configuration parameters
        @param backlog: the project stories
        @param teams: the team to receive stories to implement on next sprint
        """
        self.config = config
        self.stories = backlog
        self.teams = teams

    def generate_population(self):
        """
        Creates the starting random population for the GA algorithm.

        @config population_size: number of random solutions to generate initially
        """
        self.population = []

        for i in range(0, self.config['population_size']):
            self.population.append(self.generate_random_solution())


    def generate_random_solution(self):
        """
        Randomly creates associations between stories and teams.
        Each team will be assigned a random story until the randomly selected story
        doesn't fit in the selected team's sprint.
        """
        available_stories = self.available_stories_id()
        available_teams = list(self.teams.keys());
        teams_available_time = {key: self.teams[key]['available_time'] for key in self.teams}
        solution = []

        while len(available_stories) > 0 and len(available_teams) > 0:
            story_id = random.choice(available_stories)
            team_id = random.choice(available_teams)

            if teams_available_time[team_id] < self.stories[story_id]['time']:
                available_teams.remove(team_id)
            else:
                solution.append((team_id, story_id))
                teams_available_time[team_id] -= self.stories[story_id]['time']
                available_stories.remove(story_id)

        return solution

    def available_stories_id(self):
        """
        Returns the ids of the stories that have backlog status

        @param stories: the project stories
        """
        available_stories = []

        for story_id in self.stories:
            if self.stories[story_id]['status'] == 'backlog':
                available_stories.append(story_id)


        return available_stories

    def fitness_points(self, solution):
        """
        Calculate the fitness points for the given solution.

        Expression:
        priority * (total implemented story points) / (mean cost * (number of unimplemented dependencies * 4))

        mean cost = sum[for all stories](story points * team efficiency * team cost) / total implemented story points
        unimplemented dependencies: story that has unimplemented dependency and that dependency isn't part o the team's sprint
        """
        total_sp = sum(map(lambda x: self.stories[x]['time'], map(itemgetter(1),solution)))
        total_cost = sum(map(lambda x, y: self.stories[y]['time'] \
            * self.teams[x]['efficiency'] * self.teams[x]['cost'],
            map(itemgetter(0), solution), \
            map(itemgetter(1), solution)))
        mean_cost = total_cost / total_sp

        invalid_dependencies = 0
        for attribution in solution:
            story_dependencies = self.stories[attribution[1]]['dependency']
            for dependency_id in story_dependencies.split(','):
                if dependency_id == '':
                    continue
                elif self.stories[dependency_id]['status'] == 'working':
                    invalid_dependencies += 1
                elif self.stories[dependency_id]['status'] == 'backlog':
                    # See if dependency is in the team's sprint
                    result = list(filter(lambda x: x[1] == dependency_id, solution))
                    if len(result) != 1 or result[0][0] != attribution[0]:
                        invalid_dependencies += 1

        return total_sp / (mean_cost * 4 * invalid_dependencies)


    def run(self):
        """
        Run genetic algorithm to assign stories to teams
        """
        self.generate_population()
