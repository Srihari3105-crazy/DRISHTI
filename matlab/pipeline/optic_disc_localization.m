function od_result = optic_disc_localization(img)
%OPTIC_DISC_LOCALIZATION Pipeline wrapper for optic disc localization.
    addpath(fullfile(fileparts(mfilename('fullpath')), '..', 'segmentation'));
    od_result = optic_disc(img);
end
