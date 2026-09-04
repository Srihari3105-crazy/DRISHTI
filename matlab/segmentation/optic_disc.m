function od_result = optic_disc(img)
%OPTIC_DISC Localizes the optic nerve head using red-channel intensity and morphology.
%  Output struct:
%    mask       - binary mask (H x W)
%    center_xy  - [x y] coordinates of optic disc center
%    radius_px  - radius in pixels
%    confidence - heuristic quality metric [0, 1]

    red = double(img(:,:,1));
    [H, W] = size(red);
    red_blur = imgaussfilt(red, 5);

    non_black = red_blur(red_blur > 15);
    if isempty(non_black)
        od_result.mask = false(H, W);
        od_result.center_xy = [W/2, H/2];
        od_result.radius_px = round(min(H, W)/14);
        od_result.confidence = 0.0;
        return;
    end

    thresh_val = prctile(non_black, 92);
    bin_img = red_blur >= thresh_val;

    se = strel('disk', 12);
    bin_closed = imclose(bin_img, se);
    bin_filled = imfill(bin_closed, 'holes');

    stats = regionprops(bin_filled, 'Area', 'Centroid', 'EquivDiameter');
    if isempty(stats)
        od_result.mask = false(H, W);
        od_result.center_xy = [W/2, H/2];
        od_result.radius_px = round(min(H, W)/14);
        od_result.confidence = 0.1;
        return;
    end

    [~, max_idx] = max([stats.Area]);
    cx = round(stats(max_idx).Centroid(1));
    cy = round(stats(max_idx).Centroid(2));
    r  = round(stats(max_idx).EquivDiameter / 2);

    [X, Y] = meshgrid(1:W, 1:H);
    od_mask = ((X - cx).^2 + (Y - cy).^2) <= r^2;

    expected_r = W / 14;
    size_ratio = min(r, expected_r) / max(r, expected_r);
    conf = min(0.85, size_ratio * 0.8);

    od_result.mask = od_mask;
    od_result.center_xy = [cx, cy];
    od_result.radius_px = r;
    od_result.confidence = conf;
end
