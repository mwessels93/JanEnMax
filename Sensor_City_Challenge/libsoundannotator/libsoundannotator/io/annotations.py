class FileAnnotation(object):
    def __init__(self, wf, uid, storagetype='wav'):
        self.filename=wf
        self.uid=uid
        self.storagetype=storagetype
        self.extra_args = dict()

    def __str__(self):
        return 'FileAnnotation sourcefile: {0}  uid: {1} storagetype: {2}'.format(self.filename,self.uid, self.storagetype)
        
    def setExtraArgs(self, keys, annotation):
        for key in keys:
            if key in annotation:
                self.extra_args[key] = annotation[key]
                