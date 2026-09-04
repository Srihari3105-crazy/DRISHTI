function vessel_result = vessel_segmentation(img)
%VESSEL_SEGMENTATION Pipeline wrapper for blood vessel segmentation.
    addpath(fullfile(fileparts(mfilename('fullpath')), '..', 'segmentation'));
    vessel_result = vessels(img);
end
