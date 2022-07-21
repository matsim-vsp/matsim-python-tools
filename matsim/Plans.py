import xopen
import xml.etree.ElementTree as ET
import pandas as pd

def plan_reader(filename, selectedPlansOnly = False):
    person = None
    tree = ET.iterparse(xopen.xopen(filename), events=['start','end'])
    
    for xml_event, elem in tree:
        if elem.tag == 'person' and xml_event == 'start':
            # keep track of whether a person node has any plans
            this_person_has_plans = False

            if person: person.clear() # clear memory
            person = elem

        elif elem.tag == 'plan' and xml_event == 'end':
            this_person_has_plans = True

            # filter out unselected plans if asked to do so
            if selectedPlansOnly and elem.attrib['selected'] == 'no': continue

            yield (person, elem)

            # free memory. Otherwise the data is kept in memory
            elem.clear()
        
        elif elem.tag == 'person' and xml_event == 'end':
            # if this person has no plans, then yield the person with a None plan.
            if not this_person_has_plans:
                yield (person, None)

# Parses attributes of an element and adds them to the given dictionary
def _parseAttributes(elem, dict):
    for attrib in elem.attrib:
        dict[attrib] = elem.attrib[attrib]
    return dict

# Returns dataframes with the following columns:
# Person : ['id', 'age', 'bikeAvailability', 'carAvailability', 'censusHouseholdId', 'censusPersonId', 'employed', 'hasLicense', 'hasPtSubscription', 'householdId', 'householdIncome', 'htsHouseholdId', 'htsPersonId', 'isOutside', 'isPassenger', 'motorbikesAvailability', 'sex']
# Plan : ['id', 'person_id', 'score', 'selected']
# Activity : ['id', 'plan_id', 'type', 'link', 'facility', 'x', 'y', 'z', 'end_time', 'start_time', 'max_dur', 'typeBeforeCutting']
# Leg : ['id', 'plan_id', 'mode', 'dep_time', 'trav_time', 'routingMode']
# Route :
# TODO  - Add an option to disable parsing <attribute> xml elements
def plan_reader_dataframe(filename, selectedPlansOnly = False):
    tree = ET.iterparse(xopen.xopen(filename), events=['start','end'])
    
    persons = []
    plans = []
    activities = []
    legs = []
    routes = []
    
    currentPerson = {}
    currentPlan = {}
    currentActivity = {}
    currentLeg = {}
    currentRoute = {}
    
    # Indicates current parent element while parsing <attribute> element
    isParsingPerson = False
    isParsingActivity = False
    isParsingLeg = False
    
    currentPersonId = None
    currentPlanId = 0
    currentActivityId = 0
    currentLegId = 0
    currentRouteId = 0
    
    for xml_event, elem in tree:
        if elem.tag in ['person', 'leg', 'activity'] and xml_event == 'end':
            if isParsingPerson:
                persons.append(currentPerson)
                currentPerson = {}
                isParsingPerson = False
            
            if isParsingActivity:
                activities.append(currentActivity)
                currentActivity = {}
                isParsingActivity = False
            
            if isParsingLeg:
                legs.append(currentLeg)
                currentLeg = {}
                isParsingLeg = False
            
            elem.clear()
        
        # PERSON
        elif elem.tag == 'person':
            currentPerson['id'] = elem.attrib['id']
            currentPersonId = elem.attrib['id']
            isParsingPerson = True
        
        # PLAN
        elif elem.tag == 'plan':
            currentPlanId += 1
            
            currentPlan['id'] = currentPlanId
            currentPlan['person_id'] = currentPersonId
            currentPlan = _parseAttributes(elem, currentPlan)
            
            plans.append(currentPlan)
            currentPlan = {}
            elem.clear()
        
        # ACTIVITY
        elif elem.tag == 'activity':
            isParsingActivity = True
            currentActivityId += 1
            
            currentActivity['id'] = currentActivityId
            currentActivity['plan_id'] = currentPlanId
            currentActivity = _parseAttributes(elem, currentActivity)
            
        
        # LEG
        elif elem.tag == 'leg':
            isParsingLeg = True
            currentLegId += 1
            
            currentLeg['id'] = currentLegId
            currentLeg['plan_id'] = currentPlanId
            currentLeg = _parseAttributes(elem, currentLeg)
        
        
        # ROUTE
        elif elem.tag == 'route':
            currentRouteId += 1
            
            currentRoute['id'] = currentRouteId
            currentRoute['leg_id'] = currentLegId
            currentRoute['value'] = elem.text
            currentRoute = _parseAttributes(elem, currentRoute)
            
            routes.append(currentRoute)
            currentRoute = {}
            elem.clear()
        
        
        # ATTRIBUTES
        elif elem.tag == 'attribute' and xml_event == 'end':
            attribs = elem.attrib
            
            if isParsingActivity:
                currentActivity[attribs['name']] = elem.text
                
            elif isParsingLeg:
                currentLeg[attribs['name']] = elem.text
            
            elif isParsingPerson: # Parsing person
                currentPerson[attribs['name']] = elem.text
    
    persons = pd.DataFrame.from_records(persons)
    plans = pd.DataFrame.from_records(plans)
    activities = pd.DataFrame.from_records(activities)
    legs = pd.DataFrame.from_records(legs)
    routes = pd.DataFrame.from_records(routes)
    
    print(persons.head())
    print(plans.head())
    print(activities.head(30))
    print(legs.head())
    print(routes.head())
    # return persons
    