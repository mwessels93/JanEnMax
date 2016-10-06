#ifndef TEXTURECALCULATOR_H
#define TEXTURECALCULATOR_H

#include "thresholdCrossing.h"
#include "framescaleArray.h" 
#include "pasCalculator.h"


// context area description data types
// ... part of context area living at a single scale is given by a context interval
struct BInterval {        
        int scale;
        int runscale;
        int startFrame; 
        int endFrame;
};

// ... they are put together in to a block to form a single context area
typedef std::vector<BInterval *> BBlock;

// ... the context areas for all scales are stored in the context area vector 
typedef std::vector<BBlock *> BBlockVector;

class textureCalculator;
typedef std::map<char, textureCalculator * > textureCalculatorMap;


class textureCalculator {
    public:
        textureCalculator(pasCalculator * pas);
        textureCalculator(pasCalculator * pas, double *Bm, double *Bs,int *areasizes, int *contextAreas,int * frameoffsets, int * scaleoffsets, int noofscales, bool normalizeTexture);
        ~textureCalculator();
        void initialize();
        void calcTexture(framescaleArray * mySound);
        void getTexture(double * B);
        void getTextureStats(double *Bm, double *Bs, int *areaSizes, int *contextAreas,int * frameoffsets, int * scaleoffsets);
        static void textureCalculatorMapCleanup(textureCalculatorMap & texMap);
        
    private:
        void cleanupBBlocks();
        void deleteBBlocks (BBlockVector * BBV);
        framescaleArray * BArray;
        double * BArrayRaw;
        pasCalculator * pasCalc;
        double * BMean;
        double * BSigma;
        int * areaSize;
        int skipInitFrames;
        int skipFinalFrames;
        int  noofscales;
        int  noofframes;
        BBlockVector * BBlocks;
        bool isInitialized;
        bool BBlocksAllocated;
        void calcB4contextArea(framescaleArray * PArray, BBlock * contextArea);
        void calcBMoments(BBlock * contextArea);
        void findBlockBoundary(int scale, thresholdCrossing  * tcBase, thresholdCrossing  * tcSlope , char boundaryType, bool &runscalesValid);
        void resetBlockBoundary(int scale);
        void makeBBlockVector(double PAxisFactor, double OrthoAxisFactor);
        bool normalizeTexture;
        
        void setMargins(_margin InMargin); 
        _margin myMargins;
};





#endif // TEXTURECALCULATOR_H
