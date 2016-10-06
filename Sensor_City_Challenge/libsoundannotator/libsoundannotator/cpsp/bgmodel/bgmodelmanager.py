from bgmodel import BGModel
import numpy as np

class BGModelManager(object):
    
    def __init__(self, config):
        self.models = dict()
        for name in config:
            self.models[name] = BGModel(name,config[name])

        #energy is a model too, the fastest possible
        self.models['E'] = BGModel('E',None)
        self.models['E'].tau = 0

    def calculateChunk(self, chunk):
        for name in self.models:
            if not name == 'E':
                self.models[name].calculateChunk(chunk)
        self.models['E'].BG = chunk.data

        #now perform post-processing, subtracting models when indicated. 
        for name in self.models:
            if not name == 'E':
                self.models[name].BG = self.models[self.models[name].subtract].BG - self.models[name].BG

        #subtract 100 from E for equal masking results
        self.models['E'].BG -= 100

        #return all models concatenated vertically according to ascending tau
        model_list = sorted([self.models[name] for name in self.models], key=lambda model: model.tau)[::-1]

        return np.concatenate([model.BG for model in model_list], axis=0)
