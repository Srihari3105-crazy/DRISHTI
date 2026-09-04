function he_result = hemorrhages(img, od_mask, vessel_mask)
%HEMORRHAGES Detects intraretinal hemorrhages (dot/blot and flame hemorrhages).
%  Input:  img - uint8 RGB
%          od_mask - binary mask of optic disc
%          vessel_mask - binary mask of blood vessels (to avoid counting normal vessels)

    if nargin < 2 || isempty(od_mask), od_mask = false(size(img,1), size(img,2)); end
    if nargin < 3 || isempty(vessel_mask), vessel_mask = false(size(img,1), size(img,2)); end

    green = img(:,:,2);
    clahe_green = adapthisteq(green, 'ClipLimit', 0.02, 'NumTiles', [8 8]);

    se = strel('disk', 8);
    bothat = imbothat(clahe_green, se);

    non_zero = bothat(bothat > 0);
    if isempty(non_zero)
        thresh = 25;
    else
        thresh = max(18, prctile(non_zero, 94));
    end

    bin_he = bothat >= thresh;

    % Exclude optic disc and vessels
    bin_he(imdilate(od_mask, strel('disk', 15))) = false;
    bin_he(imdilate(vessel_mask, strel('disk', 2))) = false;

    stats = regionprops(bin_he, 'Area', 'BoundingBox');
    valid_idx = find([stats.Area] >= 50 & [stats.Area] <= 5000);
    clean_mask = ismember(bwlabel(bin_he), valid_idx);

    he_result.mask = clean_mask;
    he_result.count = length(valid_idx);
    he_result.confidence = min(0.70, length(valid_idx) / 10.0 * 0.55);
    if isempty(valid_idx)
        he_result.bboxes = zeros(0, 4);
    else
        he_result.bboxes = reshape([stats(valid_idx).BoundingBox], 4, [])';
    end
end
