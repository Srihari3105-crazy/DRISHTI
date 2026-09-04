function lesion_result = lesion_detection(img, od_result, vessel_result)
%LESION_DETECTION Orchestrates MA, EX, HE, and NV extraction.
    addpath(fullfile(fileparts(mfilename('fullpath')), '..', 'segmentation'));

    od_mask = od_result.mask;
    vessel_mask = vessel_result.mask;

    ma_res = microaneurysms(img, od_mask);
    ex_res = exudates(img, od_mask);
    he_res = hemorrhages(img, od_mask, vessel_mask);
    nv_res = neovascularization(img, od_result, vessel_mask);

    lesion_result.microaneurysms     = ma_res;
    lesion_result.exudates           = ex_res;
    lesion_result.hemorrhages        = he_res;
    lesion_result.neovascularization = nv_res;
end
