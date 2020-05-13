import xopen
import xml.etree.ElementTree as ET

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

