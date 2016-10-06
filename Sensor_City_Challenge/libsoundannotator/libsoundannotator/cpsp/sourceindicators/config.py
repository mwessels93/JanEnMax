from libsoundannotator.cpsp.bgmodel.config import getDefaults

models = [
    {
        'name': 'birds',
        'requiredKeys': ['pulse'],
        'bands': [
            ('pulse', 60, 109)
        ],
        'bgmodels': {
            'pulse': getDefaults(2, subtract='raw', mask=[0,20])
        }
    },
    {
        'name': 'car',
        'requiredKeys': ['noise', 'tone'],
        'bands': [
            ('noise', 30, 68),
            ('tone', 68, 100)
        ],
        'bgmodels': {
            'noise': getDefaults(15, subtract='raw', mask=[0,20]),
            'tone': getDefaults(2.5, subtract='raw', mask=[0,20])
        }
    }
]
"""
    {
        'name': 'speech',
        'requiredKeys': ['tone'],
        'bands': [
            ('tone', 10, 60)
        ],
        'bgmodels': {
            'tone': getDefaults(1.5, subtract='raw', mask=[-10,20])
        }
    },
    {
        'name': 'bus',
        'requiredKeys': ['noise'],
        'bands': [
            ('noise', 10, 60)
        ],
        'bgmodels': {
            'noise': getDefaults(15, subtract='raw', mask=[-10,20])
        }
    },
    {
        'name': 'scooter',
        'requiredKeys': ['tone'],
        'bands': [
            ('noise', 30, 60)
        ],
        'bgmodels': {
            'noise': getDefaults(14, subtract='raw', mask=[-10,20])
        }
    },
]"""
