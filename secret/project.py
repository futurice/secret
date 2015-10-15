import os, sys
import json

class Project:
    def __init__(self, name):
        self.name = name
        self.data = None

    def load(self):
        if self.data is None:
            try:
                data = json.loads(open(self.name, 'r').read())
            except IOError as e:
                data = {}
            self.data = data
        return self.data

    def save(self, c):
        settings = self.load()
        settings.update(**c)
        with open(self.name, 'w') as f:
            f.write(json.dumps(settings))
        self.data = None

def get_project(name):
    return Project(name=name)
