#! /usr/bin/env python

"""
Methods to build a nested lookup table containing the best paths between any
two locations on the map from a <requests> containing a FullResponse.

NOTE:   Calling best_paths() rebuilds the entire lookup table: do not call it
        repeatedly with a FullResponse, but instead save it in a table.

TODO:   Implement the lookup table as a hardcoded global hashtable, and make
        best_paths() refresh it.

Schema is as follows:

    best_paths($r)[$from][$to] -> tuple($cost, $n_actions, $commands)

where   $r          is the <requests> containing a FullResponse
        $from       is the <location> at the head (start) of the desired path
        $to         is the <location> at the tail (end) of the desired path

and     $cost       is the number of discredits that the best path costs
        $n_actions  is the number of actions required to traverse the best path
        $commands   is the list of <shellcommand>s that traverse the best path
"""

from lib.logger import *

class Map:
    
    BIKING_COST = 15    # cost of taking a bike

    BESTS = {}
    SEEDS = {}

    def __init__(self, r):
        """
        Construct a Map object which maintains an internal state corresponding
        to the map of copenhagent.

        Takes a <FullResponse> and creates internal dict with following schema:
        self.BESTS['from']['to'] == (<cost>, <num actions>, <shell commands>)
        """
        metro = self.parse_metro(r.json()['state']['map']['metro'])
        self.BESTS = {}
    
        for curr in metro.viewkeys():
            self.BESTS[curr] = {}
            for dest in metro.viewkeys():
                self.BESTS[curr][dest] = self.best_method(metro, curr, dest)

        self.update_seeds(r)

    def get_path_from_to(self, from_loc, to_loc):
        """
        Return the best path from $from_loc to $to_loc.
        """
        return self.BESTS[from_loc][to_loc][-1]

    def get_best_dest(self):
        """
        Choose the location and activity with the best seed.
        """
        def key_by_seed(item): 
            ((loc, activity), seed) = item
            val = seed
            return val

        def key_only_nav(item): 
            ((loc, activity), seed) = item
            val = seed if activity == 'navigation' else 0
            return val

        def key_only_ps(item):
            ((loc, activity), seed) = item
            val = seed if activity == 'papersoccer' else 0
            return val

        ret = max(self.SEEDS.viewitems(), key = key_by_seed)
        log('next up', ret[0])
        return ret


    def update_seeds(self, r):
        """
        Update the internal table of locations, activities, and seeds with a
        <FullResponse>.
        """
        locs = r.json()['state']['map']['locations']
        for loc in locs:
            for (ai, info) in locs[loc].get('activities', {}).viewitems():
                self.SEEDS[(loc, ai)] = info['config']['seed']
   
    
    def best_method(self, metro, curr, dest):
        """
        Takes a $parsed_metro, $curr <loc>, $dest <loc>, and returns the best path.
        Returns a tuple (<cost>, <num actions>, <shell commands>).

        Should only ever be called during initialization.
        """
        return min( self.metro_cost(metro, curr, dest, 'cw'),
                    self.metro_cost(metro, curr, dest, 'ccw'),
                    (self.BIKING_COST, 1, ['map bike locationId=%s' % dest]) )
    
    def parse_metro(self, metro): 
        """
        Returns a parsed version of r.json()['state']['map']['metro'] as follows:
    
        parsed_metro: {   locations:  {directions:    (cost, destination)}}

        Should only ever be called during initialization.
        """
        parsed = {}
        for loc in metro:
            parsed[loc] = {}
            parsed[loc]['cw'] = (   min(metro[loc]['cw'].viewvalues()), 
                                    min(metro[loc]['cw'].viewkeys())    )
            parsed[loc]['ccw'] = (  min(metro[loc]['ccw'].viewvalues()), 
                                    min(metro[loc]['ccw'].viewkeys())   )
        return parsed
    
    
    def metro_cost(self, metro, curr, dest, d):
        """
        Takes a $parsed_metro, $curr <loc>, $dest <loc>, and $d <direction>.
        Determines the cost of taking the <metro> in $d from $curr to $loc.
        Returns a tuple (<cost>, <num actions>, <shell commands>).
    
        Raises ValueError() if somehow goes around full circle or $cost passes 100.

        Should only ever be called during initialization.
        """
        walk = curr
        cost = 0
        count = 0
        while walk != dest:
            count += 1
            cost += metro[walk][d][0]
            walk = metro[walk][d][1]
            # raise errors if something goes wrong with logic
            if walk == curr: raise ValueError('smth went wrong: went full circle')
            if cost > 100:   raise ValueError('smth went wrong: cost of %d' % cost)
        return (cost, count, ['map metro direction=%s' % d for _ in range(count)])
