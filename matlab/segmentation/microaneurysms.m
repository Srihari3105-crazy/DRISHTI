function ma_result = microaneurysms(img, od_mask)
%MICROANEURYSMS Detects tiny circular red lesions via morphological small top-hat.
%  Input:  img - uint8 RGB
%          od_mask - binary mask of optic disc (to exclude bright false positives)

    if nargin < 2 || isempty(od_mask)
        od_mask = false(size(img, 1), size(img, 2));
    end

    green = img(:,:,2);
    clahe_green = adapthisteq(green, 'ClipLimit', 0.02, 'NumTiles', [8 8]);

    se = strel('disk', 3);
    bothat = imbothat(clahe_green, se);

    non_zero = bothat(bothat > 0);
    if isempty(non_zero)
        thresh = 15;
    else
        thresh = max(10, prctile(non_zero, 95));
    end

    bin_ma = bothat >= thresh;

    % Dilate OD to prevent border artefacts
    se_dil = strel('disk', 15);
    bin_ma(imdilate(od_mask, se_dil)) = false;

    stats = regionprops(bin_ma, 'Area', 'BoundingBox', 'Centroid');
    valid_idx = [];
    bboxes = [];
    for i = 1:length(stats)
        if stats(i).Area >= 3 && stats(i).Area <= 120
            valid_idx(end+1) = i;
            bboxes = [bboxes; stats(i).BoundingBox];
        end
    end

    clean_mask = ismember(bwlabel(bin_ma), valid_idx);

    ma_result.mask = clean_mask;
    ma_result.count = length(valid_idx);
    ma_result.confidence = min(0.60, length(valid_idx) / 20.0 * 0.6);
    ma_result.bboxes = bboxes;
end
