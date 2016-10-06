import json, os

class ConfigLoader(object):
    def __init__(self, filename, **kwargs):
        self.directory = kwargs.get('directory', os.path.dirname(os.path.realpath(__file__)) + '/')
        self.filename = filename

    def exists(self):
        try:
            with open(self.directory + self.filename) as jsonfile: 
                return True
        except IOError:
            return False

    def get(self):
        if not hasattr(self, 'config'):
            self.load()
        return self.config

    def load(self):
        with open(self.directory + self.filename) as json_file:
            self.config = json.load(json_file)

        json_file.close()

    def save(self, models):
        try:
            with open(self.directory + self.filename, 'wb') as json_file:
                json.dump(models, json_file)
                print "Config file written."
        except IOError, e:
            print "Oops, something went wrong with writing config: {0}. Try again".format(e)