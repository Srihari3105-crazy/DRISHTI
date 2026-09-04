function nv_result = neovascularization(img, od_result, vessel_mask)
%NEOVASCULARIZATION Heuristic detection of neovascular networks (NVD/NVE).
%  Inspects peripapillary region within 0.5 - 2.5 disc diameters for anomalous vessel density.

    [H, W, ~] = size(img);
    if isempty(od_result.center_xy) || isempty(vessel_mask)
        nv_result.mask = false(H, W);
        nv_result.count = 0;
        nv_result.confidence = 0.0;
        nv_result.bboxes = [];
        return;
    end

    cx = od_result.center_xy(1);
    cy = od_result.center_xy(2);
    r  = od_result.radius_px;

    roi_outer = round(2.5 * 2 * r);
    roi_inner = round(0.5 * 2 * r);

    [X, Y] = meshgrid(1:W, 1:H);
    dist_map = sqrt((X - cx).^2 + (Y - cy).^2);
    roi_mask = (dist_map > roi_inner) & (dist_map < roi_outer);

    vessel_in_roi = vessel_mask & roi_mask;
    roi_area = sum(roi_mask(:));

    if roi_area == 0
        density = 0;
    else
        density = sum(vessel_in_roi(:)) / roi_area;
    end

    % Heuristic threshold for anomalous vessel proliferation
    NV_THRESHOLD = 0.16;
    is_nv = density > NV_THRESHOLD;

    if is_nv
        nv_result.mask = vessel_in_roi;
        nv_result.count = 1;
        nv_result.confidence = min(0.50, density / NV_THRESHOLD * 0.40);
        nv_result.bboxes = [cx - roi_outer, cy - roi_outer, 2*roi_outer, 2*roi_outer];
    else
        nv_result.mask = false(H, W);
        nv_result.count = 0;
        nv_result.confidence = 0.0;
        nv_result.bboxes = [];
    end
end
