Chunk Alignment:

How to interpret the different parts of teh drawings presented below.

The contribution to future values (green) are data that need to be buffered on the processor, and can be used for calculation when the next chunk arrives provided that chunk is continuous with the current chunk. This purely from the perspective of the receiving processor, the smartChunks produced need to mark this green area as includedPast for the next chunk provided there is continuity.

The grey area's are data that couldn't be calculated yet despite the corresponding time was represented in the original time series for this chunk. This is specific to non-causal features, which through their inclusion of near future values can not be calculated over the full time range of the chunk.

The dark blue area's are the counterpart of the grey area's they are data that come available with the data from the next chunk.

If the calculation of the prepended history requires further history, this is not handled by composite chunks but buffered by the processor involved. See structureExctractor for an example.

Some features use information from several frequencies and these will therefore not be available at high and low freqeuncies because an insuffficient number of near frequencies is present is these area's are marked invalid.


![online processing](/media/Data/GIT_Workspace/libsoundannotator/libsoundannotator/docs/compositechunks_continuity.svg)

![lost in transmission 1](/media/Data/GIT_Workspace/libsoundannotator/libsoundannotator/docs/compositechunkslostintransmission_continuity.svg)

![lost in transmission  2](/media/Data/GIT_Workspace/libsoundannotator/libsoundannotator/docs/compositechunkslostintransmission2_continuity.svg)

![lost in transmission 3](/media/Data/GIT_Workspace/libsoundannotator/libsoundannotator/docs/compositechunkslostintransmission3_continuity.svg)

![file processing](/media/Data/GIT_Workspace/libsoundannotator/libsoundannotator/docs/compositechunks_file_continuity.svg)

![calibration](/media/Data/GIT_Workspace/libsoundannotator/libsoundannotator/docs/compositechunks_calibration_continuity.svg)


Alignment:

Design principles:

* As much as possible of the merging should be handled by the framework, leaving only processor specific data handling to the processor.

* Only valid timesteps are published, to keep alignment simple the invalid scales are included in the representation, and they can be overwritten by the receiving processor to manage problems with zero's in later calculations. 
