function fov_result = fovea_localization(img, od_result)
%FOVEA_LOCALIZATION Pipeline wrapper for fovea localization.
    addpath(fullfile(fileparts(mfilename('fullpath')), '..', 'segmentation'));
    fov_result = fovea(img, od_result);
end
