import libsoundannotator.cpsp.sourceindicators.indicator as indicator
import libsoundannotator.cpsp.bgmodel.bgmodel as bgmodel
import json, copy, numpy as np

def imscale(signal, bounds):
    signal = np.array(signal)
    #replace -inf with zero
    signal[signal == -np.inf] = 0
    signal = np.nan_to_num(signal)
    low, high = (bounds[0], bounds[1])
    if low >= high:
        raise Exception("Bounds of imscale should be [low, high] where low < high")
    signal = signal - np.min(signal)
    return (signal / (np.max(signal) / (high-low))) + low

def imgmask(signal, mask):
    signal[signal < mask[0]] = mask[0]
    signal[signal > mask[1]] = mask[1]
    return signal

"""
    Returns background models, populated model configs, and an indicator.SourceIndicator object for each of the models
    in the config's model definitions
"""
def initFromConfig(config, **kwargs):
    keys = []
    bgmodels = {}
    models = []
    for model in copy.deepcopy(config.models):
        keys = keys + model['requiredKeys']
        # hash all bg models, if we have a duplicate don't recreate it.
        # add the bg model to the model dictionary
        for key in model['bgmodels']:
            h = hash(json.dumps(model['bgmodels'][key], sort_keys=True))
            if not h in bgmodels:
                bgmodels[h] = bgmodel.BGModel(h, model['bgmodels'][key], **kwargs)
            model['bgmodels'][key] = bgmodels[h]
        models.append(model)

    indicators = []
    for model in models:
        indicators.append(indicator.SourceIndicator(model, **kwargs))
    return indicators, models, bgmodels

"""
    Calculates leaky-integrated responses based on indicator definitions
"""
def calculateBGModels(inputs, indicators, bgmodels, normalize=False):
    #transform each key in inputs to a leaky-integrated one
    #keep track of inputs we have calculated
    responses = dict((h, None) for h in bgmodels)
    for i in indicators:
        keys = i.wants()
        for key in keys:
            #bg model hash
            h = i.model['bgmodels'][key].name
            #do we need to calculate the response?
            if responses[h] is None:
                if not key in inputs:
                    raise Exception("Indicator {} wants key {} for comparison, but key is not present in input".format(i.name, key))
                if normalize:
                    inputsignal = imscale(inputs[key], [0,60])
                    response = bgmodels[h].calculate(inputsignal)
                else:
                    response = bgmodels[h].calculate(inputs[key])
                    inputsignal = inputs[key]

                if bgmodels[h].subtract is not None:
                    if bgmodels[h].subtract == 'raw':
                        response = inputs[key] - response
                    else:
                        raise Exception('Not yet possible to subtract anything other than original ("Raw")')
                if bgmodels[h].mask is not None:
                    responses[h] = imgmask(response, bgmodels[h].mask)
                else:
                    responses[h] = response
            #pass the reference to response to indicator
            i.setBGModel(key, responses[h])
