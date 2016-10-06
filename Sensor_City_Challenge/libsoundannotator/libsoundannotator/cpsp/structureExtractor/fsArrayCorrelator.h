#ifndef FSARRAYCORRELATOR_H
#define FSARRAYCORRELATOR_H

#include "thresholdCrossing.h"
#include "framescaleArray.h"

class fsArrayCorrelator{
    public:
        fsArrayCorrelator( int noofframes, int maxframedelay, int noofscales, double * fsa);
        ~fsArrayCorrelator();
         // Functions and variables for correlation calculations
        bool calcCorrelation(int framedelay,int scale,int xscale , double &xcorr);
        thresholdCrossing * scanLineFromOrigin(int scale,int dscale, int dframe, double * correlationMatrix);
        thresholdCrossing * scanLineFromOrigin(int scale,double dscale, double dframe,int (*pMap2IntFunction)(double), double * correlationMatrix);
        bool updateMatrixIfValid(double &prevxcorr, double &xcorr,int delay, int scale, int xscale, double * correlationMatrix);
		
    private:
        int maxframedelay;
        int noofdelays;
        int noofscales;
        int noofframes;
        double * means; 
        double * stddevs;
        double * squares;
        framescaleArray* fsArray;
        void initialize();
};

#endif // FSARRAYCORRELATOR_H

