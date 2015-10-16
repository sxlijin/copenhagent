#! /usr/bin/env python

##### AI FUNCTIONS <START> #####




def program():
    #this shit is to do the map enter, map metro, and map bike commands and update loc internally
    a= try_command('map enter').json()
    set_loc( a['state']['agents'][AGENT_TOKEN]['locationId'] )
    metroLine = a['state']['map']['metro']
    print ('Your starting location is ')+LOCATION 

    b= try_command('map metro').json()
    message =b['action']['message'].split();
    set_loc( message[4] )
    incr_dis_credits( -int(message[8]) )
    print ('Current discredits: ')+str(DIS_CREDITS)
    print ('Current location: ')+LOCATION

    c= try_command('map bike').json()
    message =c['action']['message'].split();
    set_loc( message[4] )
    incr_dis_credits( int(message[8]) )
    print ('Current location: ')+LOCATION
    print ('Current discredits: ')+str(DIS_CREDITS)


    #this guy is to find what's cheaper, to metro it or to bike
    dest=raw_input('tell me where u wanna go yo: ')
    while(dest not in metroLine.keys()):
        print('FOOL THAT\'S NOT A VALID LOCATION')
        print('Try that again. Here\'s your options cuz you can\'t remember probably.')
        print metroLine.keys()
        dest=raw_input('gimme that location: ')
    curLocation=LOCATION
    #clockwise:
    cwCost=0
    while(curLocation!=dest):
        tempLocation=metroLine[curLocation]['cw'].keys()[0]
        cwCost+=metroLine[curLocation]['cw'][tempLocation]
        curLocation=tempLocation
    print 'The cost to get from ' +LOCATION + ' to '+dest+ ' with the metro in cw order is '+ str(cwCost)+'.'
    #counterclockwise
    ccwCost=0
    curLocation=LOCATION
    while(curLocation!=dest):
        tempLocation=metroLine[curLocation]['ccw'].keys()[0]
        ccwCost+=metroLine[curLocation]['ccw'][tempLocation]
        curLocation=tempLocation
    print 'The cost to get from ' +LOCATION + ' to '+dest+' with the metro in ccw order is '+ str(ccwCost)+'.'
    cost=15
    cheapest='bike'
    print "cwcost is {}, ccwcost is {}".format(cwCost, ccwCost)
    if(cwCost<cost):
        cost=cwCost
        if(ccwCost<cost):
            cheapest='ccw metro'
        else:
            cheapest='cw metro'
    elif(ccwCost<cost):
        cheapest='ccw metro'
    print 'the cheapest way to get to ' + dest+ ' is to '+cheapest


