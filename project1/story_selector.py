# Copyright 2016 (C) Thiago Pinto.
#
# This software may be modified and distributed under the terms
# of the MIT license.  See the LICENSE file for details.

__author__ = "Thiago Pinto"

import random


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

    def __init__(self, config):
        """
        Initialize global data structures

        @param config: algorithm configuration parameters
        """
        self.config = config

    def generate_population(self, stories, teams):
        """
        Creates the starting random population for the GA algorithm.

        @config population_size: number of random solutions to generate initially
        @param stories: the project stories
        @param teams: the team to receive stories to implement on next sprint
        """

    def available_stories_id(self, stories):
        """
        Returns the ids of the stories that have backlog status

        @param stories: the project stories
        """
        available_stories = []

        for story_id in stories:
            if stories[story_id]['status'] == 'backlog':
                available_stories.append(story_id)


        return available_stories


    def generate_random_solution(self, stories, teams):
        """
        Randomly creates associations between stories and teams.
        Each team will be assigned a random story until the randomly selected story
        doesn't fit in the selected team's sprint.

        @param stories: the project stories
        @param teams: the team to receive stories to implement on next sprint
        """
        available_stories = self.available_stories_id(stories)
        available_teams = list(teams.keys());
        teams_available_time = {key:teams[key]['available_time'] for key in teams}
        solution = []

        while len(available_stories) > 0 and len(available_teams) > 0:
            story_id = random.choice(available_stories)
            team_id = random.choice(available_teams)

            if teams_available_time[team_id] < stories[story_id]['time']:
                available_teams.remove(team_id)
            else:
                solution.append((story_id, team_id))
                teams_available_time[team_id] -= stories[story_id]['time']
                available_stories.remove(story_id)

        return solution
