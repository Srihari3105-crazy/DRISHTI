function fov_result = fovea(img, od_result)
%FOVEA Geometric localization of the fovea centralis relative to optic disc.
%  Fovea is located approximately 2.5 OD diameters temporal to the disc center.

    [H, W, ~] = size(img);

    if isempty(od_result.center_xy) || isempty(od_result.radius_px) || od_result.radius_px == 0
        fov_result.center_xy = [round(W/2), round(H/2)];
        fov_result.confidence = 0.1;
        fov_result.method = 'image_center_fallback';
        return;
    end

    cx = od_result.center_xy(1);
    cy = od_result.center_xy(2);
    r  = od_result.radius_px;
    od_diam = 2 * r;

    % Temporal displacement (assumes right eye OD; clamp to bounds)
    fovea_x = min(W - 1, max(1, round(cx + 2.5 * od_diam)));
    fovea_y = min(H - 1, max(1, round(cy + 0.05 * od_diam)));

    fov_result.center_xy = [fovea_x, fovea_y];
    fov_result.confidence = 0.40;  % Geometric estimate heuristic
    fov_result.method = 'geometric_2.5_od_diameters_temporal';
end
