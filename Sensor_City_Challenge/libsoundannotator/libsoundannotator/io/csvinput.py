import csv, os

class CSVInputReader(object):
    
    def __init__(self, filepath):
        if not os.path.isfile(filepath):
            raise Exception("No such file: {}".format(filepath))
        
        self.filepath = filepath
        self.rows = None
        self.headers = None
        
    def read(self):
        if self.rows != None and self.headers != None:
            return self.headers, self.rows
        else:
            with open(self.filepath, 'rb') as fh:
                try:
                    self.rows = []
                    self.headers = []
                    self.reader = csv.DictReader(fh, delimiter=',')
                    for row in self.reader:
                        self.rows.append(row)
                    self.headers = self.rows[0].keys()
                    return self.headers, self.rows
                except Exception as e:
                    raise e