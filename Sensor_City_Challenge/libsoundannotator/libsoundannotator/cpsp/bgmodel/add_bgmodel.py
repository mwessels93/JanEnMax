import libsoundannotator.cpsp as cpsp

from cpsp.bgmodel.bgmodelprocessor import ConfigLoader
import json
import sys

exists = False

text = {
	'delta_time': "Delta time: \n",
	'tau':"Specify time constant:\n",
	'step':"Specify time step:\n",
	'noiseSTD':"Specify noiseSTD:\n",
	'FBR_scope':"FBR scope min and max, comma separated (like -10,10):\n",
	'FBR_range': "FBR range min and max, comma separated (like -20, 20):\n",
}

try:
	with open('config.json') as configfile:
		exists = True
except IOError:
	pass

loader = ConfigLoader('config.json')

if loader.exists():
	print "List of current models:\n"
	models = loader.get()
	for model in models:
		print "\n{0}\n\ttc: {1}\n\tFBR_scope: {2}\n\tFBR_range: {3}\n\tstep: {4}\n\tnoiseSTD: {5}\n\tdelta time: {6}\n\tsubtract: {7}\n".format(model, models[model]['tau'],models[model]['FBR_scope'],models[model]['FBR_range'],models[model]['step'],models[model]['noiseSTD'],models[model]['delta_time'], models[model]['subtract'])
	print "\n\n"
else:
	print "No known models"
	models = dict()

def catch_q_or_return(i):
	val = raw_input(i)
	if  val == 'q':
		sys.exit()
	else:
		return val

def update_model():
	name = catch_q_or_return("Available models: {0}.\nType name to edit. Press 'q' to quit: ".format(", ".join([name for name in models])))
	
	while name not in models:
		name = catch_q_or_return("Name doesn't exits in models. Try again or press 'q' to quit:\n")
		
	model = models[name]

	print "Specify which parameter to edit. Press 'q' to quit:\n"

	for idx,key in zip(range(len(model)), sorted(model.keys())):
		print "{0}: {1}".format(idx,key)

	idx = int(catch_q_or_return(": "))

	while idx >= len(model):
		idx = int(catch_q_or_return("Wrong index given. Try again or press 'q' to quit: \n: "))

	key = sorted(model.keys())[idx]

	print "Updating {0}:{1}".format(key,model[key])

	if key == 'subtract':
		newval = get_subtract()
	elif key in ['FBR_scope','FBR_range']:
		newval = [float(val) for val in raw_input(text[key]).split(',')]
	else:
		newval = float(raw_input(text[key]))

	loader.save(models)

def delete_model():
	name = raw_input("Existing models: {0}.\nType name to delete: ".format(", ".join([name for name in models])))
	while name not in models:
			name = catch_q_or_return("Name doesn't exits in models. Try again or press 'q' to quit:\n")

	del models[name]
	print "Model is deleted"

	loader.save(models)

def create_model():
	name = raw_input("Name for new model: \n")

	while name in models:
		name = catch_q_or_return("Model {0} already exists. Specify other name or press 'q' to quit:\n")

	delta_time = float(raw_input(text['delta_time']))
	tau = float(raw_input(text['tau']))
	FBR_scope = [float(val) for val in raw_input(text['FBR_scope']).split(',')]
	FBR_range = [float(val) for val in raw_input(text['FBR_range']).split(',')]
	step = float(raw_input(text['step']))
	noiseSTD = float(raw_input(text['noiseSTD']))
	subtract = get_subtract()


	models[name] = {
		'delta_time': delta_time,
		'tau': tau,
		'FBR_scope' : FBR_scope,
		'FBR_range' : FBR_range,
		'step' : step,
		'noiseSTD' : noiseSTD,
		'subtract' : subtract,
	}

	loader.save(models)

def get_subtract():
	subtract = 'E'
	if len(models) > 0:
		do_subtract = raw_input("Subtract existing model? 'n' reverts to default, subtracting the energy (y/n)\n")
		if do_subtract == 'y':
			print "Select model to subtract:"
			print "\n- ".join([name for name in sorted(models)])
			which = raw_input(": ")
			while not which in models:
				which = raw_input("Given model does not exist. Try again or press 'n' to skip:\n")
				if which == 'n':
					which = 'E'
					break
			subtract = which

	return subtract

def run():
	while True:
		action = catch_q_or_return("Choose action: {0}\n".format("u = update model, c = create model, d = delete model, q = quit"))
		if action == 'u':
			update_model()
		elif action == 'c':
			create_model()
		elif action == 'd':
			delete_model()
		else:
			print "Unknown action\n"

#run app
run()

