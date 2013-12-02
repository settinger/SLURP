"""
Classes used for storing the semantic
structures generated by the semantic parser.
"""

# Copyright (C) 2011-2013 Kenton Lee, Constantine Lignos, and Ian Perera
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from semantics.util import text2int, is_pronoun

class Entity(object):
    """Parent class of entities"""

    TYPES = ['Object', 'Location']
    TYPE_ID = -1  # Subclasses should override TYPE_ID

    def __init__(self, name=None, description=None):
        self.name = name
        self.quantifier = Quantifier()
        # Using mutable object as default argument causes
        # it to be aliased across instances
        self.description = description if description is not None else []
        
    def merge(self, other):
        """Merge this entity with another entity"""
        if other.name is not None:
            self.name = other.name
        self.quantifier.merge(other.quantifier)
        self.description.extend(other.description)

    def readable(self, case=True):
        # case: true for subject false for object
        if self.name == '*':
            return 'I' if case else 'me'
        elif is_pronoun(self.name):
            return self.name
        else:
            return '%s %s' % (self.quantifier.readable(), self.name)
        
    def __str__(self, lvl=0):
        if self.name == '*':
            return self.name
        indent = '\t'*(lvl)
        return str(self.TYPES[self.TYPE_ID]) + '\n'+ \
            indent + '\tName: ' + str(self.name) + '\n' + \
            indent + '\tQuantifier: ' + (self.quantifier.__str__(lvl + 1) if self.quantifier else '') + '\n' + \
            indent + '\tDescription: ' + str(self.description)
            
    def __dict__(self):
        return { str(self.TYPES[self.TYPE_ID]): \
                {
                 'Name' : self.name , \
                 'Quantifier' : (self.quantifier.__dict__() if self.quantifier else '') , \
                 'Description' : self.description
                }
                }

    def __repr__(self):
        return str(self)

    def __hash__(self):
        return hash(self.name)

class ObjectEntity(Entity):
    """Class representing an object entity"""

    TYPE_ID = 0
    def __eq__(self,other):
        return (isinstance(other,ObjectEntity) and
                self.name == other.name and
                self.quantifier == other.quantifier and
                self.description == other.description
                )
        
    @staticmethod
    def from_dict(d):
        default = ObjectEntity(d["Name"],d["Description"])
        quantifier = Quantifier.from_dict(d["Quantifier"])       
        default.description = d["Description"] 
        default.quantifier = quantifier
        return default


class Location(Entity):
    """Class representing a location entity"""

    TYPE_ID = 1
    
    def __eq__(self,other):
        return (isinstance(other,Location) and
                self.name == other.name and
                self.quantifier == other.quantifier and
                self.description == other.description
                )
        
    @staticmethod
    def from_dict(d):
        default = Location(d["Name"],d["Description"])
        quantifier = Quantifier.from_dict(d["Quantifier"])   
        default.description = d["Description"]     
        default.quantifier = quantifier
        return default


class Quantifier(object):
    """Class representing a quantifier"""

    # Exactly one parameter should be specified at a time
    def __init__(self, dt=None, cd=None):
        if dt in ('any', 'some'):
            self.definite = False
            self.type = 'any'
            self.number = None
        elif dt in ('a', 'an'):
            self.definite = False
            self.type = 'exact'
            self.number = 1
        elif dt in ('none', 'no'):
            self.definite = True
            self.type = 'none'
            self.number = 0
        elif dt in ('all', 'each'):
            self.definite = True
            self.type = 'all'
            self.number = None
        else:  # When dt is 'the', None, or unknown
            # Lowest priority when merging
            self.definite = True
            self.type = 'exact'
            self.number = 1
        if cd != None:
            self.number = cd if cd.isdigit() else text2int(cd)
            
    def __eq__(self,other):
        return (isinstance(other,Quantifier) and
                self.type == other.type and
                self.definite == other.definite and
                self.number == other.number
                )
        
    @staticmethod
    def from_dict(d):
        default = Quantifier()
        default.type = d["Type"]
        default.definite = d["Definite"]
        default.number = d["Number"]
        return default 

    def readable(self):
        if self.definite:
            if self.type == 'all':
                return self.type
            if self.number == 0:
                return 'no'
            if self.number == 1:
                return 'the'
            else:
                return str(self.number)
        else:
            if self.number == 1:
                return 'a'
            else:
                return 'any'

    def __str__(self, lvl=0):
        indent = '\t'*(lvl)
        return '\n' + indent + '\tDefinite: %s\n' % str(self.definite) + \
               indent + '\tType: %s\n' % str(self.type) +\
               indent + '\tNumber: %s' % str(self.number)
               
    def __dict__(self):
        return { 'Definite' : self.definite ,\
               'Type' : str(self.type) ,\
               'Number' : self.number
               }        

    def fill_determiner(self, dt):
        """Fills self with a determiner by merging it with
        a new quantifier created with that determiner"""
        self.merge(Quantifier(dt=dt))

    def fill_cardinal(self, cd):
        """Fills self with a cardinal number  by merging it with
        a new quantifier created with that cardinal number"""
        self.merge(Quantifier(cd=cd))

    def merge(self, other):
        """Merge quantifier with other quantifer"""

        # Assume combination of definite and indefinite is definite
        # e.g. some of the rooms
        self.definite = self.definite and other.definite

        # Non-exact types and numbers should take precedence
        if other.type in ('any', 'none', 'all'):
            self.type = other.type

        if other.number != 1:
            self.number = other.number

    def __repr__(self):
        return str(self)


class Assertion(object):
    """Asserts the existence or property of an Entity in the world."""

    def __init__(self, theme, location, existential=False):
        self.theme = theme
        self.location = location
        self.existential = existential

    def readable(self):
        return '{!r} is/are in {!r}'.format(self.theme.readable(case=True), self.location.readable())

    def __str__(self, lvl=0):
        indent = '\t'*(lvl)
        return 'Assertion: \n' + \
            (indent + '\tTheme: %s\n' % self.theme.__str__(lvl + 1) if self.theme else '') + \
            (indent + '\tLocation: %s\n' % self.location.__str__(lvl + 1) if self.location else '')+ \
            indent + '\tExistential: %s' % str(self.existential)

    def __repr__(self):
        return str(self)


class Query(object):
    """Base class for all queries"""
    def __repr__(self):
        return str(self)

class YNQuery(Query):
    """Yes/No queries."""
    def __init__(self, theme, location):
        self.theme = theme
        self.location = location

    def __str__(self, lvl=0):
        indent = '\t'*(lvl)
        return 'YNQuery: \n' + \
               indent + '\tTheme: %s\n' % self.theme.__str__(lvl + 1) + \
               indent + '\tLocation: %s' % self.location.__str__(lvl + 1)


class LocationQuery(Query):
    """Where queries"""
    def __init__(self, theme):
        self.theme = theme

    def __str__(self, lvl=0):
        indent = '\t'*(lvl)
        return '\n' + indent + 'LocationQuery: \n' + \
               indent + '\tTheme: %s\n' % self.theme.__str__(lvl + 1)


class StatusQuery(Query):
    """Status queries"""
    def __init__(self):
        pass
    def __str__(self, lvl=0):
        return 'StatusQuery'

class EntityQuery(Query):
    """Who/What queries"""
    def __init__(self, location):
        self.location = location

    def __str__(self, lvl=0):
        indent = '\t'*(lvl)
        return 'EntityQuery: \n' + \
               indent + '\tLocation: %s\n' % self.location.__str__(lvl + 1)


class Command(object):
    """A Command for Junior to do something."""

    def __init__(self, agent, theme, patient, location, source, destination, action,
                 condition=None, negation=False):
        self.agent = agent
        self.theme = theme
        self.patient = patient
        self.location = location
        self.source = source
        self.destination = destination
        self.action = action
        self.condition = condition
        self.negation = negation
        
    def __str__(self, lvl=0):
        indent = '\t'*(lvl + 1)
        return 'Command: \n' + \
               (indent + 'Agent: ' + self.agent.__str__(lvl + 1) + '\n' if self.agent else '') + \
               indent + 'Action: ' + str(self.action)  + '\n' + \
               (indent + 'Theme: ' + self.theme.__str__(lvl + 1) + '\n' if self.theme else '') + \
               (indent + 'Patient:' + self.patient.__str__(lvl + 1) + '\n' if self.patient else '') + \
               (indent + 'Location: ' + self.location.__str__(lvl + 1) + '\n' if self.location else '') + \
               (indent + 'Source: ' + self.source.__str__(lvl + 1) + '\n' if self.source else '') + \
               (indent + 'Destination: ' + self.destination.__str__(lvl + 1) + '\n' if self.destination else '') + \
               (indent + 'Condition: ' + self.condition.__str__(lvl + 1) + '\n' if self.condition else '') + \
               indent + 'Negation: ' + str(self.negation)
               
    def __dict__(self):
                return{ 'Command': { \
               'Agent' : (self.agent.__dict__() if self.agent else ''),  \
               'Action' : str(self.action) ,\
               'Theme' : (self.theme.__dict__() if self.theme else ''), \
               'Patient' : (self.patient.__dict__() if self.patient else ''), \
               'Location' : (self.location.__dict__() if self.location else ''), \
               'Source' : (self.source.__dict__() if self.source else ''), \
               'Destination' : (self.destination.__dict__() if self.destination else ''), \
               'Condition' : (self.condition.__dict__() if self.condition else ''), \
               'Negation' : self.negation}}
                
    def __eq__(self,other):
        # TODO: consolidate this, useful for debugging for now
        z = isinstance(other,Command)
        a = self.agent == other.agent             
        b = self.action == other.action
        c = self.theme == other.theme
        d = self.patient == other.patient
        e = self.location == other.location
        f = self.source == other.source
        g = self.destination == other.destination
        h = self.condition == other.condition
        i = self.negation == other.negation
        return z and a and b and c and d and e and f and g and h and i
    
    def __repr__(self):
        return str(self)

    def readable(self):
        response = ''
        if self.negation:
            response += ' not'
        if not self.action:
            return ''
        else:
            response += ' %s' % self.action
        if self.theme:
            response += ' %s' % self.theme.readable(case=False)
        elif self.patient:
            response += ' %s' % self.patient.readable(case=False)
        if self.location:
            response += ' in %s' % self.location.readable()
        if self.source:
            response += ' from %s' % self.source.readable()
        if self.destination:
            response += ' to %s' % self.destination.readable()
        if self.condition:
            response += ' if %s' % self.condition.readable()
        return response

class Event(object):
    """An event in the environment."""

    def __init__(self, theme, sensor):
        self.theme = theme
        self.sensor = sensor

    def __str__(self, lvl=0):
        indent = '\t'*(lvl)
        return 'Event:\n' + \
               indent + '\tSensor: ' + str(self.sensor) + '\n' + \
               (indent + '\tTheme: ' + self.theme.__str__(lvl + 1) if self.theme else '')

    def __repr__(self):
        return str(self)

    def readable(self):
        return 'I %s %s' % (self.sensor, self.theme.readable(case=False))
