#ifndef THRESHOLDCROSSING_H
#define THRESHOLDCROSSING_H
#include <vector>

class thresholdCrossing {
    public:
        thresholdCrossing( int sp, int fp, double xp, int sb, int fb, double xb, double d, int s, int ctr ): \
                            scale_center(ctr), scale_super(sp),frame_super(fp), xcorr_super(xp),\
                            scale_sub(sb), frame_sub(fb), xcorr_sub(xb), \
                            delta(d), status(s){
                            };
        thresholdCrossing( thresholdCrossing* tc); 
        thresholdCrossing( thresholdCrossing* tc, double factor); 
        
        // center scale
        int scale_center;
                        
        // Last superthreshold point in line scan
        int scale_super;
        int frame_super;
        double xcorr_super;
        
        // First subthreshold point in line scan
        int scale_sub;
        int frame_sub;
        double xcorr_sub;
        
        // Best estimate for real location of threshold (threshold)  on the line starting from the last superthreshold point in the correlation matrix (cm)to the first subthreshold point.
        double delta;     // delta=threshold-cm(scale_super,frame_super)/(cm(scale_sub,frame_sub)-cm(scale_super,frame_super))
        //std::vector <double> lineDirection;
    
        static int iroundaway( double x); // round away from zero
        static int ifloor(double arg);
        static int iceil(double arg);
        
        static thresholdCrossing* merge (thresholdCrossing*, thresholdCrossing*);
        static double threshold;
        
        // Line scan mechanisms need to return a value even if the scan ends prematurely on the edge of the TS plane or the scan is ill posed, e.g. zero increment
        int status;
        
        // Status values
        static int const found=1;
		static int const notfound=2;
		static int const illegalsearch=3;
};

// derived data types



#endif //THRESHOLDCROSSING_H
