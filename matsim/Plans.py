import gzip
import xml.etree.ElementTree as ET

def plan_reader(filename, selectedPlansOnly = False):

    person = None
    tree = ET.iterparse(gzip.open(filename), events=['start','end'])

    for xml_event, elem in tree:

        if elem.tag == 'person' and xml_event=='start':
            if person: person.clear() # clear memory
            person = elem

        elif elem.tag == 'plan' and xml_event=='end':
            # filter out unselected plans if asked to do so
            if selectedPlansOnly and elem.attrib['selected'] == 'no': continue

            yield (person, elem)
            # free memory. Otherwise the data is kept in memory
            elem.clear()
