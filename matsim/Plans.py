import xopen
import xml.etree.ElementTree as ET
import pandas as pd


class Plans:
    def __init__(self, persons, plans, activities, legs, routes):
        self.persons = persons
        self.plans = plans
        self.activities = activities
        self.legs = legs
        self.routes = routes

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

# Returns dataframes with the following relations between them:
# Person : None
# Plan : person_id
# Activity : plan_id
# Leg : plan_id
# Route :leg_id
# The column names of the dataframes are the same as the attribute names (<name:'value'> and <attribute> are parsed)
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
        if elem.tag in ['person', 'leg', 'activity', 'plan', 'route'] and xml_event == 'end':
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
            
            if elem.tag == 'plan':
                if elem.attrib['selected'] == 'no' and selectedPlansOnly: continue
                plans.append(currentPlan)
                currentPlan = {}
                
            if elem.tag == 'route':
                routes.append(currentRoute)
                currentRoute = {}
            
            elem.clear()
        
        # PERSON
        elif elem.tag == 'person':
            currentPerson['id'] = elem.attrib['id']
            currentPersonId = elem.attrib['id']
            isParsingPerson = True
        
        # PLAN
        elif elem.tag == 'plan':
            if elem.attrib['selected'] == 'no' and selectedPlansOnly: continue
            currentPlanId += 1
            
            currentPlan['id'] = currentPlanId
            currentPlan['person_id'] = currentPersonId
            currentPlan = _parseAttributes(elem, currentPlan)
        
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
    
    return Plans(persons, plans, activities, legs, routes)
    