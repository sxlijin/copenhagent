#! /usr/bin/env python

import sys

metro = {
    "dis": {
        "cw": {
            "koedbyen": 3
        },
        "ccw": {
            "folketinget": 1
        }
    },
    "koedbyen": {
        "cw": {
            "frederiksberg": 5
        },
        "ccw": {
            "dis": 3
        }
    },
    "frederiksberg": {
        "cw": {
            "louises": 9
        },
        "ccw": {
            "koedbyen": 5
        }
    },
    "louises": {
        "cw": {
            "noerrebrogade": 1
        },
        "ccw": {
            "frederiksberg": 9
        }
    },
    "noerrebrogade": {
        "cw": {
            "jaegersborggade": 2
        },
        "ccw": {
            "louises": 1
        }
    },
    "jaegersborggade": {
        "cw": {
            "parken": 5
        },
        "ccw": {
            "noerrebrogade": 2
        }
    },
    "parken": {
        "cw": {
            "langelinie": 9
        },
        "ccw": {
            "jaegersborggade": 5
        }
    },
    "langelinie": {
        "cw": {
            "christianshavn": 8
        },
        "ccw": {
            "parken": 9
        }
    },
    "christianshavn": {
        "cw": {
            "bryggen": 5
        },
        "ccw": {
            "langelinie": 8
        }
    },
    "bryggen": {
        "cw": {
            "folketinget": 5
        },
        "ccw": {
            "christianshavn": 5
        }
    },
    "folketinget": {
        "cw": {
            "dis": 1
        },
        "ccw": {
            "bryggen": 5
        }
    }
}

new_metro = {}

for loc in metro:
    new_metro[loc] = {}
    new_metro[loc]['cw'] = (min(metro[loc]['cw'].viewvalues()), min(metro[loc]['cw'].viewkeys()))
    new_metro[loc]['ccw'] = (min(metro[loc]['ccw'].viewvalues()), min(metro[loc]['ccw'].viewkeys()))


def metro_cost(curr, dest, d):
    walk = curr
    cost = 0
    count = 0
    while walk != dest:
        count += 1
#        print 'going from', walk, 'to',
        cost += new_metro[walk][d][0]
        walk = new_metro[walk][d][1]
#        print walk, 'and have now cost', str(cost)
#        if cost > 50: break
    
#    print 'cost from', curr, 'to', dest, 'via', d, 'is', str(cost)
    return (cost, count, ['map metro direction=%s' % d for i in range(count)])

locs = metro.viewkeys()

def best_method(curr, dest):
    return min( metro_cost(curr, dest, 'cw'),
                metro_cost(curr, dest, 'ccw'),
                (15, 1, 'map bike locationId=%s' % dest) )

best_paths = {}

for curr in locs:
    best_paths[curr] = {}
    for dest in locs:
        best_paths[curr][dest] = best_method(curr, dest)

print best_paths
