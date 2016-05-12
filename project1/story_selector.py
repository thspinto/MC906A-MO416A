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
        solution = []

        while len(available_stories) > 0:
            story_id = random.choice(available_stories)
            team_id = random.choice(list(self.teams.keys()))

            solution.append({'team_id': team_id, 'story_id': story_id})
            available_stories.remove(story_id)

        return {'solution': solution, 'fitness_points': self.fitness_points(solution)}


    def available_stories_id(self, solution=[]):
        """
        Returns the ids of the stories that have backlog status, and are not
        assined to any team on @param solution

        @param solution: the story assignmet to each team
        """
        available_stories = []

        for story_id in self.stories:
            if self.stories[story_id]['status'] == 'backlog':
                available_stories.append(story_id)

        for attribution in solution:
            if attribution['story_id'] in available_stories:
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
        if(len(solution) == 0):
            return 0

        total_sp = sum(map(lambda x: self.stories[x['story_id']]['time'], solution))
        total_cost = sum(map(lambda x: self.stories[x['story_id']]['time'] \
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

        available_stories = self.available_stories_id(solution)
        if(len(available_stories) == 0):
            rand = 1
        else:
            rand = random.random()
            story_id = random.choice(available_stories)
            team_id = random.choice(list(self.teams))
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


    def reproduce(self):
        """
        Reproduces the population.

        reproduction_proportion new solutions are created and added to the population.

        @config reproduction_type: the type of reproduction {tournament, roulette}
        """
        reproduction_type = self.config['reproduction_type']
        self.new_population = []
        for i in range(len(self.population)):
            if reproduction_type == 'tournament':
                self.tournament_reproduction()
            elif reproduction_type == 'roulette':
                fitness_sum = sum(map(lambda x: x['fitness_points'], self.population))
                self.roulette_reproduction(fitness_sum)
            elif reproduction_type == 'none':
                self.mutation_reproduction(self.population[i])


    def mutation_reproduction(self, solution):
        """
        Just copy and mutate individuals.

        @param solution: the solution to be copied and maybe mutated
        """
        mutation_probability = self.config['mutation_probability']
        new_solution = list(solution['solution'])
        rand = random.random()
        if(rand < mutation_probability):
            self.mutation(new_solution)
        self.new_population.append({'solution': new_solution, \
            'fitness_points': self.fitness_points(new_solution)})



    def tournament_reproduction(self):
        """
        Reproduction by tournament.

        Two groups of reproduction_group_size solutions are selected randomly,
        the best fit of each group is selected for reproduction.

        @config reproduction_tournament_size: the size o the reproduction group to find
        the best fit
        """

        parentA = random.choice(self.population)
        parentB = random.choice(self.population)
        for x in range(self.config['reproduction_tournament_size'] - 1):
            competitorA = random.choice(self.population)
            competitorB = random.choice(self.population)

            if(parentA['fitness_points'] < competitorA['fitness_points']):
                parentA = competitorA
            if(parentB['fitness_points'] < competitorB['fitness_points']):
                parentB = competitorB

        self.new_population.append(self.crossover(parentA, parentB))


    def roulette_reproduction(self, fitness_sum):
        """
        Reproduction by roullete.

        Chooses two individuals using the following algorithm.

        @algorithm: Gerenates a random number R between 0 and fitness_sum. Then
        iterates through the population until the cumulative sum of the fitness_points
        is more than R. The individual of the iteration that satisfies that condition
        is the choosen one.
        """

        rA = random.randrange(int(fitness_sum))
        rB = random.randrange(int(fitness_sum))

        parentA = None
        parentB = None
        accumulator = 0
        for solution in self.population:
            accumulator += solution['fitness_points']
            if accumulator > rA and parentA is None:
                parentA = solution
            if accumulator > rB and parentB is None:
                parentB = solution
            if parentA is not None and parentB is not None:
                break

        self.new_population.append(self.crossover(parentA, parentB))

    def crossover(self, solutionA, solutionB):
        """
        Creates a new solution, crossingover solutionA and solutionB.

        The crossover algorithm randomly chooses crossover_cutpoints on each solution.
        The attribution between the first and secondo cutpoint (or the end of the array)
        are switched between the two solutions.

        After crossover the new individual might be mutated depending on the probability
        defined by the configuration mutation_probability.

        @param solutionA, solutionB: the two solutions that will be crossedover
        @config mutation_probability: the probability of the new individual being mutated
        """
        mutation_probability = self.config['mutation_probability']
        max_len = max(len(solutionA['solution']), len(solutionB['solution']))
        cutpoints = [random.randrange(max_len + 1)]
        cutpoints.append(cutpoints[0] + 1)

        cutpoints = sorted(cutpoints)
        cutB = solutionB['solution'][cutpoints[0]:cutpoints[1]]

        #Copy slutionA
        new_solution = list(solutionA['solution'])
        #Insert solutionB's cut in solutionA
        new_solution[cutpoints[0]:cutpoints[1]] = cutB

        rand = random.random()
        if(rand < mutation_probability):
            self.mutation(new_solution)

        self.remove_duplicate_stories(new_solution)

        return {'solution': new_solution, 'fitness_points': self.fitness_points(new_solution)}

    def remove_duplicate_stories(self, solution):
        """
        Removes repeated assignments in solution.

        @param solution: the solution to be cleaned
        """
        stories = []
        for assignment in solution:
            if assignment['story_id'] not in stories:
                stories.append(assignment['story_id'])
            else:
                solution.remove(assignment)

    def select(self):
        """
        Creates a new population merging the new solutions.

        @config selection_strategy: The strategy to create the new population.
        Accepted set {elitism, substitution}
        """
        selection_strategy = self.config['selection_strategy']

        if selection_strategy == 'elitism':
            self.elitism_select()
        elif selection_strategy == 'steadyState':
            self.steady_state()

    def elitism_select(self):
        """
        Creates the new population using the following algorithm.

        @algorithm Elitism: the new populations will be composed by 9/10 the best
        new solutions plus 1/10 best fit of the old generation.
        """
        elitism_size = int(len(self.population) / 10)
        new_population = sorted(self.population, \
            key=lambda x: x['fitness_points'], reverse=True)[:elitism_size]
        new_population.extend(sorted(self.new_population, \
            key=lambda x: x['fitness_points'])[elitism_size:])

        self.population = new_population


    def steady_state(self):
        """
        Creates the new population using the following algorithm.

        @algorithm Substitution: The N wost solutions will be substituted by the
        new solutions.
        """
        ss_size = int(len(self.population) / 10)
        new_population = sorted(self.new_population, \
            key=lambda x: x['fitness_points'], reverse=True)[:ss_size]
        new_population.extend(sorted(self.population, \
            key=lambda x: x['fitness_points'])[ss_size:])

        self.population = new_population


    def run(self):
        """
        Run genetic algorithm to assign stories to teams
        """

        self.generate_population()
        print('-----------Init--------------')
        print(self.config)

        for i in range(100):
            self.reproduce()
            self.select()

            sorted_population = sorted(self.population, \
                key=lambda x: x['fitness_points'])
            print(sorted_population[0]['fitness_points'])
            print(sorted_population[-1]['fitness_points'])
            print((sorted_population[0]['fitness_points'] + \
                    sorted_population[-1]['fitness_points']) / 2 )
        #print(sum(map(lambda x: x['fitness_points'], self.population))/len(self.population))
            print("============")
