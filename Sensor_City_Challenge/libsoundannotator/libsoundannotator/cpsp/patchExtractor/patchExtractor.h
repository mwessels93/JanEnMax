#ifndef PATCHEXTRACTOR_H
#define PATCHEXTRACTOR_H

#include "framescaleArray.h"

class patchExtractor {
    public:
        
        patchExtractor();
        ~patchExtractor();
        int setTimeScaleData(int noofRows,int noofCols, int *textures, int *patches); // M stands for Matlab, in anticipation of P for Python
        void copyTimeScaleData(int *textures, int *patches);
        
        int getSimplePatchDescriptors(int noofRows, int noofCols, int * pPatchDescriptors);
        
        int getNoOfPatches(){return noPatches;};
        int getNoOfCols(){return noofCols;};
        int getNoOfRows(){return noofRows;};
        void getInColCount(int componentNo, int * ColCountVector);
        int getColsInPatch(int patchNo);
        void getInRowCount(int componentNo, int * RowCountVector);
        int getRowsInPatch(int patchNo);
        int getMasks(int patchNo, int noofRows, int noofCols, int *masks);   
        int calcInPatchMeans(int noofRows, int noofCols, double * TF_Observable);
        void getInColDist(int componentNo, double * ColDistVector);
        void getInRowDist(int componentNo, double * RowDistVector);
        int calcJoinMatrix(int noofContiguous, int * TexturesBefore, int * texturesAfter, int * PatchNumbersBefore , int * PatchNumbersAfter, int * JoinMatrix );
        bool simpleDescriptorsAllocated;
        
    private:
        int FindRoot (int k, int *par);
        int Link (int p, int q, int *par);
        int ConnectedComponentLabeling(int noofContiguous, int noofMajors, int **im); 
        int calcSimplePatchDescriptors(); 
        void clearSimplePatchDescriptors(); 
        int ** ppTSPatched;
        bool ppTSPatchedSet;
        int noofCols, noofRows;
        int noPatches;
        int * textureType, *lowerCol, *upperCol, *lowerRow, * upperRow , *fullCount;

        int ** InRowCounts, **InColCounts;
        double ** InRowDist, **InColDist;
        bool inPatchMeansSet;
        void clearInPatchMeans();
        void JoinLink (int lowPatch, int highPatch, int lastvalidPatchNo,int *joinMatrix) ;
};
#endif
