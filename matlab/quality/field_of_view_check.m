function [fov_detected, fov_coverage, center_radius] = field_of_view_check(img)
%FIELD_OF_VIEW_CHECK Detects circular retinal boundary using Hough Transform.
%  Requires: Computer Vision Toolbox (imfindcircles)

    if size(img, 3) == 3
        green = uint8(img(:,:,2));
    else
        green = uint8(img);
    end

    [H, W] = size(green);
    total_px = H * W;
    min_r = round(min(H, W) * 0.25);
    max_r = round(min(H, W) * 0.65);

    fov_detected = false;
    fov_coverage = 0;
    center_radius = [W/2, H/2, min(H,W)/2];

    try
        [centers, radii, ~] = imfindcircles(green, [min_r max_r], ...
            'ObjectPolarity', 'bright', 'Sensitivity', 0.92, 'Method', 'TwoStage');
        if ~isempty(radii)
            [~, idx] = max(radii);
            cx = centers(idx, 1);
            cy = centers(idx, 2);
            r = radii(idx);
            center_radius = [cx, cy, r];

            [X, Y] = meshgrid(1:W, 1:H);
            circle_mask = ((X - cx).^2 + (Y - cy).^2) <= r^2;
            fov_coverage = sum(circle_mask(:)) / total_px;
            fov_detected = true;
        else
            non_black = green > 15;
            fov_coverage = sum(non_black(:)) / total_px;
        end
    catch
        non_black = green > 15;
        fov_coverage = sum(non_black(:)) / total_px;
    end
end
