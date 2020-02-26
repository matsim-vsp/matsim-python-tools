import gzip
import xml.etree.ElementTree as ET


def event_reader(filename, filter=None):
    """
    Return a generator of events from the specified file.
    Each event will be generated as a dictionary of attribute key/value pairs.
    Any content text of the XML element itself is dropped, as MATSim events are attribute-only.

    filter: event types to return. Can be a list, set, or comma-separated string. Default None returns all events.
    """

    # set up event filter - so that we only yield useful events
    if filter == None:
        keep = None
    elif isinstance(filter, set) or isinstance(filter, list):
        keep = filter
    else:
        keep = set(filter.split(','))

    tree = ET.iterparse(gzip.open(filename))

    try:
        for xml_event, elem in tree:
            attributes = elem.attrib

            if elem.tag == 'event':
                # skip events we don't care about
                if keep:
                    if not attributes['type'] in keep: continue

                # got one! yield the event to the caller
                attributes['time'] = float(attributes['time'])
                yield attributes

            # free memory. Otherwise the data is kept in memory and we loose the advantage of streaming
            elem.clear()

    except Exception as e:
        # Why am I catching this exception instead of allowing it to propagate up?
        # Because some event files (**coughswitzerland**) are badly formed and do not contain
        # the closing </events> tag at the end of the file. If we don't trap that error, the
        # entire analysis fails.
        print('*** XML ERROR:', e)
