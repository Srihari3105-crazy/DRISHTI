function ex_result = exudates(img, od_mask)
%EXUDATES Detects bright lipid deposits (hard exudates) outside the optic disc.
%  Input:  img - uint8 RGB
%          od_mask - binary mask of optic disc

    if nargin < 2 || isempty(od_mask)
        od_mask = false(size(img, 1), size(img, 2));
    end

    lab = rgb2lab(img);
    L = lab(:,:,1);

    se = strel('disk', 10);
    tophat = imtophat(L, se);

    non_zero = tophat(tophat > 0);
    if isempty(non_zero)
        thresh = 20;
    else
        thresh = max(15, prctile(non_zero, 85));
    end

    bin_ex = tophat >= thresh;

    % Exclude optic nerve head
    se_dil = strel('disk', 20);
    bin_ex(imdilate(od_mask, se_dil)) = false;

    stats = regionprops(bin_ex, 'Area', 'BoundingBox');
    valid_idx = find([stats.Area] >= 10);
    clean_mask = ismember(bwlabel(bin_ex), valid_idx);

    ex_result.mask = clean_mask;
    ex_result.count = length(valid_idx);
    ex_result.confidence = min(0.65, length(valid_idx) / 15.0 * 0.5);
    if isempty(valid_idx)
        ex_result.bboxes = zeros(0, 4);
    else
        ex_result.bboxes = reshape([stats(valid_idx).BoundingBox], 4, [])';
    end
end
