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
                solution.append({'team_id': team_id, 'story_id': story_id})
                teams_available_time[team_id] -= self.stories[story_id]['time']
                available_stories.remove(story_id)

        return solution


    def available_stories_id(self, solution=[]):
        """
        Returns the ids of the stories that have backlog status

        @param stories: the project stories
        """
        available_stories = []

        for story_id in self.stories:
            if self.stories[story_id]['status'] == 'backlog':
                available_stories.append(story_id)

        for attribution in solution:
            available_stories.remove(attribution['story_id'])

        return available_stories


    def fitness_points(self, solution):
        """
        Calculate the fitness points for the given solution.

        @param solution: a solution from a population

        Expression:
        priority * (total implemented story points) / (mean cost * (number of unimplemented dependencies * 4))

        mean cost: sum[for all stories](story points * team efficiency * team cost) / total implemented story points
        unimplemented dependencies: story that has unimplemented dependency and that dependency isn't part o the team's sprint
        """
        total_sp = sum(map(lambda x: self.stories[x['story_id']]['time'], solution))
        total_cost = sum(map(lambda x, y: self.stories[x['story_id']]['time'] \
            * self.teams[x['team_id']]['efficiency'] \
            * self.teams[x['team_id']]['cost'], solution))
        mean_cost = total_cost / total_sp

        excess_hours = self.excess_hours(solution)

        invalid_dependencies = 0
        for attribution in solution:
            story_dependencies = self.stories[attribution['story_id']]['dependency']
            for dependency_id in story_dependencies.split(','):
                if dependency_id == '':
                    continue
                elif self.stories[dependency_id]['status'] == 'working':
                    invalid_dependencies += 1
                elif self.stories[dependency_id]['status'] == 'backlog':
                    # See if dependency is in the team's sprint
                    result = list(filter(lambda x: x['story_id'] == dependency_id, solution))
                    if len(result) != 1 or result[0]['team_id'] != attribution['team_id']:
                        invalid_dependencies += 1

        return total_sp / (1 + (mean_cost * 4 * invalid_dependencies * excess_hours))


    def excess_hours(self, solution):
        """
        Get the total excess hours done by the teams

        @param solution: a solution from a population
        """
        total_hours = {}
        for assingment in solution:
            hours = self.stories[assingment['story_id']]['time'] \
            * self.teams[assingment['team_id']]['efficiency']
            if assingment['team_id'] not in total_hours:
                total_hours[assingment['team_id']] = hours
            else:
                total_hours[assingment['team_id']] += hours

        excess_hours = 0
        for key in total_hours:
            hours = total_hours[key] - self.teams[key]['available_time']
            if hours > 0:
                excess_hours += hours

        return excess_hours

    def mutation(self, solution):
        """
        Mutates the solution.

        There are 3 types of mutation:
        1. A new attribution (team, story) is created by randomly selecting a
        team an available story.
        2. An existing attribution is modified, changing team or the story with
        equal probability. If the story is changed, it with be exchange with a
        random available story
        3. An existing probability is deleted.
        """
        rand = random.random()
        story_id = random.choice(self.available_stories_id(solution))
        team_id = random.choice(list(self.teams))
        print(rand)
        if(rand < 1/3):
            # Add new attribution
            solution.append({'team_id': team_id, 'story_id': story_id})
        elif(rand < 2/3):
            # Edit an attribuiton
            attribution = random.choice(solution)
            if(random.random() < 1/2):
                # Edit team
                attribution['team_id'] = team_id
            else:
                # Edit story
                attribution['story_id'] = story_id
        else:
            # Remove an attribution
            del solution[random.randrange(len(solution))]


    def run(self):
        """
        Run genetic algorithm to assign stories to teams
        """
        self.generate_population()
