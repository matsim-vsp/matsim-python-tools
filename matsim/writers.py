import numpy as np
from typing import Dict, Union, Collection, TypeVar

Id = TypeVar('Id', str, int)


class XmlWriter:
    NO_SCOPE = -1
    attributes_current_scope = -2
    ATTRIBUTES_SCOPE_FACTOR = 13
    scope = 0

    def __init__(self, writer):
        self.writer = writer
        self.indent = 0
        self.set_scope(self.NO_SCOPE)

    def _write_line(self, content: str):
        self._write_indent()
        self._write(content + "\n")

    def _write_indent(self):
        self._write("  " * self.indent)

    def _write(self, content: str):
        self.writer.write(bytes(content, "utf-8"))

    def _require_scope(self, scope: int):
        if scope == self.NO_SCOPE and self.scope != self.NO_SCOPE:
            raise RuntimeError("Expected initial scope")

        if not self.scope == scope:
            raise RuntimeError("Expected different scope")

    def set_scope(self, scope: int):
        # print(f"scope {self.scope} -> {scope}")
        self.scope = scope

    def start_attributes(self, expected_scope: int = None):
        if expected_scope is None:  # not checking scope
            expected_scope = self.scope
        self._require_scope(expected_scope)
        self._write_line('<attributes>')
        self.indent += 1
        self.attributes_current_scope = expected_scope * self.ATTRIBUTES_SCOPE_FACTOR
        self.set_scope(self.attributes_current_scope)

    def end_attributes(self):
        self._require_scope(self.attributes_current_scope)
        self.indent -= 1
        self.set_scope(int(self.attributes_current_scope / self.ATTRIBUTES_SCOPE_FACTOR))
        self._write_line('</attributes>')

    def add_attribute(self, name: str, value: Union[str, int, float, bool], typ: str = None):
        if not typ:
            typ = self.get_java_type(type(value))
        self._require_scope(self.attributes_current_scope)
        self._write_line(f'<attribute name="{name}" class="{typ}">{value}</attribute>')

    @staticmethod
    def yes_no(value: bool):
        return "yes" if value else "no"

    @staticmethod
    def true_false(value: bool):
        return "true" if value else "false"

    @staticmethod
    def time(time: int):
        if np.isnan(time):
            return None

        time = int(time)
        hours = time // 3600
        minutes = (time % 3600) // 60
        seconds = (time % 60)
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"

    @staticmethod
    def get_java_type(python_type: type):
        if 'float' in str(python_type):
            return "java.lang.Double"
        elif 'int64' in str(python_type):
            return "java.lang.Long"
        elif 'int' in str(python_type):
            return "java.lang.Integer"
        elif 'str' in str(python_type):
            return "java.lang.String"
        elif 'bool' in str(python_type):
            return "java.lang.Boolean"
        else:
            return "java.lang.Object"

    def write_preamble_attributes(self, attributes: dict):
        self.start_attributes(expected_scope=0)
        for name, value in attributes.items():
            self.add_attribute(name, value)
        self.end_attributes()


class PopulationWriter(XmlWriter):
    POPULATION_SCOPE = 0
    FINISHED_SCOPE = 1
    PERSON_SCOPE = 2
    PLAN_SCOPE = 3

    def __init__(self, writer):
        XmlWriter.__init__(self, writer)

    def start_population(self, attributes: Dict[str, str] = None):
        self._require_scope(self.NO_SCOPE)
        self._write_line('<?xml version="1.0" encoding="utf-8"?>')
        self._write_line('<!DOCTYPE population SYSTEM "http://www.matsim.org/files/dtd/population_v6.dtd">')
        self._write_line('<population>')
        self.set_scope(self.POPULATION_SCOPE)
        self.indent += 1
        if attributes is not None:
            self.write_preamble_attributes(attributes)

    def end_population(self):
        self._require_scope(self.POPULATION_SCOPE)
        self.indent -= 1
        self._write_line('</population>')
        self.set_scope(self.FINISHED_SCOPE)

    def start_person(self, person_id: Id, attributes: Dict[str, str] = None):
        self._require_scope(self.POPULATION_SCOPE)
        self._write_line(f'<person id="{person_id}">')
        self.set_scope(self.PERSON_SCOPE)
        self.indent += 1
        if attributes:
            self.start_attributes(expected_scope=self.PERSON_SCOPE)
            for k, v in attributes.items():
                self.add_attribute(k, v)
            self.end_attributes()

    def end_person(self):
        self._require_scope(self.PERSON_SCOPE)
        self.indent -= 1
        self.set_scope(self.POPULATION_SCOPE)
        self._write_line('</person>')

    def start_plan(self, selected: bool):
        self._require_scope(self.PERSON_SCOPE)
        self._write_line(f'<plan selected="{self.yes_no(selected)}">')
        self.indent += 1
        self.set_scope(self.PLAN_SCOPE)

    def end_plan(self):
        self._require_scope(self.PLAN_SCOPE)
        self.indent -= 1
        self.set_scope(self.PERSON_SCOPE)
        self._write_line('</plan>')

    def add_activity(self, type: str, x: float, y: float, facility_id: str = None,
                     start_time: int = None, end_time: int = None, attributes: dict = None):
        self._require_scope(self.PLAN_SCOPE)
        self._write_indent()
        self._write('<activity ')
        self._write(f'type="{type}" ')
        self._write(f'x="{x}" y="{y}" ')
        if facility_id is not None: self._write(f'facility="{facility_id}" ')
        if start_time is not None: self._write(f'start_time="{self.time(start_time)}" ')
        if end_time is not None: self._write(f'end_time="{self.time(end_time)}" ')
        if attributes:
            self._write('>\n')
            self.indent += 1
            self.start_attributes(expected_scope=self.PLAN_SCOPE)
            for k, v in attributes.items():
                self.add_attribute(k, v)
            self.end_attributes()
            self.indent -= 1
            self._write_line('</activity>')
        else:
            self._write('/>\n')

    def add_leg(self, mode: str, departure_time: int = None, travel_time: int = None, attributes: dict = None):
        self._require_scope(self.PLAN_SCOPE)
        self._write_indent()
        self._write('<leg ')
        self._write(f'mode="{mode}" ')
        if departure_time is not None: self._write(f'dep_time="{self.time(departure_time)}" ')
        if travel_time is not None: self._write(f'trav_time="{self.time(travel_time)}" ')
        if attributes:
            self._write('>\n')
            self.indent += 1
            self.start_attributes(expected_scope=self.PLAN_SCOPE)
            for k, v in attributes.items():
                self.add_attribute(k, v)
            self.end_attributes()
            self.indent -= 1
            self._write_line('</leg>')
        else:
            self._write('/>\n')


class HouseholdsWriter(XmlWriter):
    HOUSEHOLDS_SCOPE = 0
    FINISHED_SCOPE = 1
    HOUSEHOLD_SCOPE = 2

    def __init__(self, writer):
        XmlWriter.__init__(self, writer)

    def start_households(self, attributes=None):
        self._require_scope(self.NO_SCOPE)
        self._write_line('<?xml version="1.0" encoding="utf-8"?>')
        self._write_line('<households xmlns="http://www.matsim.org/files/dtd" '
                         'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" '
                         'xsi:schemaLocation="http://www.matsim.org/files/dtd '
                         'http://www.matsim.org/files/dtd/households_v1.0.xsd">')
        self.set_scope(self.HOUSEHOLDS_SCOPE)
        self.indent += 1
        if attributes is not None:
            self.write_preamble_attributes(attributes)

    def end_households(self):
        self._require_scope(self.HOUSEHOLDS_SCOPE)
        self._write_line('</households>')
        self.set_scope(self.FINISHED_SCOPE)

    def start_household(self, household_id: Id):
        self._require_scope(self.HOUSEHOLDS_SCOPE)
        self._write_line(f'<household id="{household_id}">')
        self.set_scope(self.HOUSEHOLD_SCOPE)
        self.indent += 1

    def end_household(self):
        self._require_scope(self.HOUSEHOLD_SCOPE)
        self.indent -= 1
        self.set_scope(self.HOUSEHOLDS_SCOPE)
        self._write_line('</household>')

    def add_members(self, person_ids: Collection[Id]):
        self._require_scope(self.HOUSEHOLD_SCOPE)
        self._write_line('<members>')
        self.indent += 1
        for person_id in person_ids:
            self._write_line(f'<personId refId="{person_id}" />')
        self.indent -= 1
        self._write_line('</members>')

    def add_income(self, income: Union[float, int]):
        self._require_scope(self.HOUSEHOLD_SCOPE)
        self._write_line(f'<income currency="CHF" period="month">{income}</income>')


class FacilitiesWriter(XmlWriter):
    FACILITIES_SCOPE = 0
    FINISHED_SCOPE = 1
    FACILITY_SCOPE = 2

    def __init__(self, writer):
        XmlWriter.__init__(self, writer)

    def start_facilities(self, attributes=None):
        self._require_scope(self.NO_SCOPE)
        self._write_line('<?xml version="1.0" encoding="utf-8"?>')
        self._write_line('<!DOCTYPE facilities SYSTEM "http://www.matsim.org/files/dtd/facilities_v1.dtd">')
        self._write_line('<facilities>')
        self.set_scope(self.FACILITIES_SCOPE)
        self.indent += 1
        if attributes is not None:
            self.write_preamble_attributes(attributes)

    def end_facilities(self):
        self._require_scope(self.FACILITIES_SCOPE)
        self.indent -= 1
        self._write_line('</facilities>')
        self.set_scope(self.FINISHED_SCOPE)

    def start_facility(self, facility_id: Id, x: float, y: float):
        self._require_scope(self.FACILITIES_SCOPE)
        self._write_line(f'<facility id="{facility_id}" x="{x}" y="{y}">')
        self.indent += 1
        self.set_scope(self.FACILITY_SCOPE)

    def end_facility(self):
        self._require_scope(self.FACILITY_SCOPE)
        self.indent -= 1
        self.set_scope(self.FACILITIES_SCOPE)
        self._write_line('</facility>')

    def add_activity(self, purpose: str):
        self._require_scope(self.FACILITY_SCOPE)
        self._write_line(f'<activity type="{purpose}" />')

