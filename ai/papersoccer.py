#! /usr/bin/env python


def win_k_is_0_papersoccer():
    win_from = {    'n': [  'papersoccer play direction=ne',
                            'papersoccer play direction=s',
                            'papersoccer play direction=ne',
                            'papersoccer play direction=se',
                            'papersoccer play direction=se' ] ,
                    's': [  'papersoccer play direction=se',
                            'papersoccer play direction=n',
                            'papersoccer play direction=se',
                            'papersoccer play direction=ne',
                            'papersoccer play direction=ne' ]       }
    
    def ps_force_win_from(side):
        for act in win_from[side]: r = try_command(act)
        # uncomment to pause before leaving the game
        # raw_input('press enter to leave papersoccer game ')
        try_command('papersoccer leave')
        return r
        
    def ps_play_dir(direction):
        return try_command('papersoccer play direction=' + direction)
    
    def ps_win():
        dirs = ['ne','se']
        rand2 = randint(0,1)
    
        r = try_command('papersoccer enter')
        r = ps_play_dir(dirs[rand2])
        # try a random direction
        if len(r.json()['action']['percepts']) == 2:
            rand2 -= 1
            for i in range(2): r = ps_play_dir(dirs[rand2])
            if len(r.json()['action']['percepts']) == 2:
                rand2 -= 1
                r = ps_play_dir(dirs[rand2])
                r = ps_play_dir('e')
                r = ps_force_win_from(
                    r.json()['action']['percepts'][0][0])
        if r.json()['action']['percepts'] == ['w']:
            r = ps_force_win_from(dirs[rand2][0])
        if not SILENT: print '\n', r.json()['action']['message']

def win_k_is_0_papersoccer():
    win_from_1 = {  'n': [  'papersoccer play direction=ne',
                            'papersoccer play direction=se',
                            'papersoccer play direction=se' ] ,
                    's': [  'papersoccer play direction=se',
                            'papersoccer play direction=ne',
                            'papersoccer play direction=ne' ]       }
    
    def ps_force_win_from(side):
        for act in win_from[side]: r = try_command(act)
        # uncomment to pause before leaving the game
        # raw_input('press enter to leave papersoccer game ')
        try_command('papersoccer leave')
        return r
        
    def ps_play_dir(direction):
        return try_command('papersoccer play direction=' + direction)
    
    def ps_win():
        dirs = ['ne','se']
        rand2 = randint(0,1)
    
        r = try_command('papersoccer enter')
        r = ps_play_dir(dirs[rand2])
        # try a random direction
        if len(r.json()['action']['percepts']) == 2:
            rand2 -= 1
            for i in range(2): r = ps_play_dir(dirs[rand2])
            if len(r.json()['action']['percepts']) == 2:
                rand2 -= 1
                r = ps_play_dir(dirs[rand2])
                r = ps_play_dir('e')
                r = ps_force_win_from(
                    r.json()['action']['percepts'][0][0])
        if r.json()['action']['percepts'] == ['w']:
            r = ps_force_win_from(dirs[rand2][0])
        if not SILENT: print '\n', r.json()['action']['message']


