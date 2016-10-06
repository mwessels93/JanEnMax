#ifndef PASCALCULATOR_H
#define PASCALCULATOR_H

#include "thresholdCrossing.h"
#include "framescaleArray.h" 

#include <vector>
#include <map>

// threshold crossing pairs, should be found by searching the correlation matrix in two opposite directions 
class  thresholdPair{
    public:
        thresholdPair(){};
        ~thresholdPair(){};
        thresholdPair(thresholdCrossing * tc1_, thresholdCrossing * tc2_ ): tc1(tc1_),tc2(tc2_){};
        thresholdPair(const thresholdPair& pb ): tc1(pb.tc1),tc2(pb.tc2){};
        static void cleanup( thresholdPair & tp){ delete tp.tc1; delete tp.tc2;};
        thresholdCrossing * tc1;
        thresholdCrossing * tc2;
};

// each scale has a pair of threshold crossing pairs
typedef std::vector<thresholdPair> thresholdPairVector;

class pasCalculator;
typedef std::map<char, pasCalculator * > pasCalculatorMap;

class pasCalculator {
    public:
        pasCalculator();
        pasCalculator(bool normalize);
        ~pasCalculator();
        
        void initialize(bool bWhite, framescaleArray * fsa);
        void calcPas(framescaleArray * fsa);
        void getPasStats( double *Pm, double *Ps, int * tcSamplePoints,\
            int * tcStatus, double * tcInterpolationDeltas,\
            int * frameoffsets, int * scaleoffsets );
        void setPasStats( double *Pm, double *Ps, int * tcSamplePoints,\
            int * tcStatus, double * tcInterpolationDeltas,\
            int * frameoffsets, int * scaleoffsets );
            
        void setDimensions(int ns);
        void getDimensions(int & ns);
        void getPas(double *P );
        
        thresholdPairVector thresholdsPAxis;
        thresholdPairVector thresholdsOrthoAxis;
        framescaleArray * PArray;
        bool isNormalized();
        int noofscales;
        int noofframes;
        static void pasCalculatorMapCleanup( pasCalculatorMap & pMap);
        
        _margin getMargins(); 

        
    private:
        void calcPMoments(bool bWhite ,framescaleArray * fsa);
        void calcP4Scale(int scale,  thresholdCrossing* tc1, thresholdCrossing * tc2,  framescaleArray * fsa);
        void setMargins(_margin InMargin); 
        _margin myMargins;
        
        double * PMean;
        double * PSigma;
        bool isInitialized;
        bool normalizePas;
  
        double * PArrayRaw;
};





#endif // PASCALCULATOR_H
