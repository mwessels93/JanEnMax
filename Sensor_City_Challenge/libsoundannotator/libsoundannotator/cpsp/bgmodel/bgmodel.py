import numpy as np, math, logging

class BGModel(object):

    def setdefaults(self, parameters):
        if parameters is not None:
            self.delta_time = parameters['delta_time'] #seconds, must be the timestep between consecutive values of EdB.

            # The core idea is to vary the Leaky Integration timeconstant tau as
            # function of local FG to BG ratio. The FG is always the energy
            # (but in a variant it can be any faster BG-model).

            # The BG is the leaky integrated energy of the previous time step. Leaky
            # integration entails that at each timestep a fraction (according to an exponential
            # decay with a given tau) is lost, while the (energy) value for this point in time
            # is added while being weighted by 1 - the same fraction.
            #
            # BG(t) = BG(t-1)*loss + EdB(t)*(1-loss)        (1)
            #
            # In this case the loss is foreground-background ratio (FBR) dependent The background
            # models to be calculated are each determined by a time constant belonging
            # to a forgeound-background ratio (FBR) of 0 dB.

            self.tau = parameters['tau']

            # When the FBR (foreground background ratio) is negative (and the
            # background is higher than the foreground) the leaky integration forgets
            # fast and follows the energy more closely. When the FBR is positive the
            # background is (as it is supposed to be) smaller than the foreground and
            # the time constant is increased so that the background approaches the
            # energy less fast.

            # FGBGR negative : very short tc
            # FGBGR with crit of zero: tc as specified
            # FGBGR > crit : longer tc

            self.FBR_SCOPE= parameters['FBR_scope']    # dB determines minimal and maximal effectivev change of tau
            self.FBR_RANGE= parameters['FBR_range']    # Determins the minimal and maximal FBR differences that influence tau

            self.step = parameters['step']                    # Determines the number of point in table for effective tau and loss

            # As a refinement we can treat all values around 0 dB FBR with the same
            # time constant. The range depends on the (frequency dependent)
            # standardeviation of a noisy signal in that channel.

            self.noiseSTD= parameters['noiseSTD']                      # should be channel dependent and computed from real data.

            self.subtract = parameters['subtract']
            self.mask = parameters['mask']

    def __init__(self, name, parameters, **kwargs):
        self.name = name
        self.setdefaults(parameters)

        if 'logger' in kwargs:
            self.logger = kwargs.get('logger')
        else:
            self.logger = logging.getLogger('BGModel')

        # Initialization BG-models
        # Mainly table of FG/BG ration dependent time constants and their effect on
        # leaky integration

        self.FBR_values = np.arange(self.FBR_RANGE[0],self.FBR_RANGE[1], 0.1)

        # Correction flat between -self.noiseSTD < FBR < +self.noiseSTD
        # idx of first element in condition value > -self.noiseSTD. [0][0] returns the index from the tuple.
        indLow = [(idx,val) for idx,val in enumerate(self.FBR_values) if val > -self.noiseSTD][0][0]
        # idx of first element in condition value > self.noiseSTD. [0][0] returns the index from the tuple.
        indHigh= [(idx,val) for idx,val in enumerate(self.FBR_values) if val > self.noiseSTD][0][0]

        col1 = np.linspace(self.FBR_SCOPE[0],0, indLow)
        col2 = np.linspace(0,0,indHigh-indLow)
        col3 = np.linspace(0,self.FBR_SCOPE[1],len(self.FBR_values)-indHigh)

        #bmat notation is confusing, this will just be a (1, X) vector
        self.FBR_cor = np.power(10,(0.1*np.bmat('col1 col2 col3')))

        # The effective loss results from an adaptation of
        # tc-effective = tc*FBR_cor

        self.loss = np.power(math.e, (-self.delta_time/(np.transpose(self.FBR_cor) * self.tau)))  # Mote matix multiplication: result numel(tau)*numel(FRR_SCOPE)

    def calculate(self, E, skip=1):
        self.logger.info("Signal shape {}".format(E.shape))
        #initialize BG
        self.BG = np.zeros((E.shape[0],E.shape[1]),dtype=float)
        if skip == 1:
            #first 100ms is the energy. current implementation: first time series is the energy
            self.BG[:,0] = E[:,0]
            self.prevBG = self.BG[:,0]

        for idx in range(skip,E.shape[1]):
            fbr = E[:,idx] - self.prevBG #Approximate local FBR
            # Limit to scope. This can be prevent by making FBR_scope really big
            # TODO: find out why sometimes 'nan' appears here. For now, filter it out
            fbr = np.nan_to_num(np.clip(fbr, self.FBR_RANGE[0],self.FBR_RANGE[1]))
            # Compute loss vector
            loss_lookup = np.floor( (fbr - self.FBR_SCOPE[0]) / self.step ).astype(int) + 1

            loss = np.ravel(self.loss[loss_lookup])

            self.BG[:,idx] = self.prevBG * loss + E[:,idx] * (1 - loss)
            #save BG response at this idx as last response
            self.prevBG = self.BG[:,idx]

        return self.BG
