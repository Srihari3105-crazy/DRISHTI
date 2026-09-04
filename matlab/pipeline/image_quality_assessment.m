function result = image_quality_assessment(img)
%IMAGE_QUALITY_ASSESSMENT  Assess fundus image quality.
%
%  RESULT = IMAGE_QUALITY_ASSESSMENT(IMG)
%
%  Computes three independent quality metrics:
%    1. Focus/sharpness: Tenengrad gradient energy on green channel
%    2. Illumination:    Mean and distribution of green channel histogram
%    3. Field of View:   Circular Hough transform to detect retinal disc
%
%  Uses Image Processing Toolbox: fspecial, imfilter, imfindcircles
%
%  Returns struct with fields:
%    focus_score      - Tenengrad energy (higher = sharper)
%    laplacian_var    - Variance of Laplacian (secondary focus)
%    illum_mean       - Mean green channel value [0,255]
%    overexposed_frac - Fraction pixels > 250
%    underexposed_frac- Fraction pixels < 30
%    fov_coverage     - Fraction of image inside retinal circle
%    fov_detected     - Boolean
%    decision         - 'QUALITY_GOOD' | 'QUALITY_BORDERLINE' | 'QUALITY_UNGRADABLE'
%    feedback         - Cell array of specific feedback strings
%    validated        - false (thresholds not yet clinically validated)
%
%  Thresholds (must be validated on a labelled quality dataset):
%    FOCUS_PASS  = 150   (Tenengrad energy)
%    FOCUS_FAIL  = 60
%    ILLUM_LOW   = 60    (mean pixel value)
%    ILLUM_HIGH  = 210
%    FOV_PASS    = 0.55  (coverage fraction)
%    FOV_FAIL    = 0.35

    % ── Thresholds ──────────────────────────────────────────────────────────
    FOCUS_PASS  = 150;
    FOCUS_FAIL  = 60;
    ILLUM_LOW   = 60;
    ILLUM_HIGH  = 210;
    OVEREXP_FRAC = 0.10;
    UNDEREXP_FRAC = 0.20;
    FOV_PASS    = 0.55;
    FOV_FAIL    = 0.35;

    % ── Extract green channel ────────────────────────────────────────────────
    if size(img, 3) == 3
        green = double(img(:,:,2));
    else
        green = double(img);
    end
    [H, W] = size(green);
    total_px = H * W;

    % ── 1. Focus: Tenengrad ─────────────────────────────────────────────────
    % Sobel operators (Image Processing Toolbox: fspecial)
    sobel_h = fspecial('sobel');
    sobel_v = sobel_h';
    Gx = imfilter(green, sobel_h, 'replicate');
    Gy = imfilter(green, sobel_v, 'replicate');
    tenengrad = mean(Gx(:).^2 + Gy(:).^2);

    % Laplacian variance (secondary metric)
    lap_filter = fspecial('laplacian', 0);
    lap_img = imfilter(green, lap_filter, 'replicate');
    laplacian_var = var(lap_img(:));

    % ── 2. Illumination ──────────────────────────────────────────────────────
    illum_mean = mean(green(:));
    overexposed_frac  = sum(green(:) > 250) / total_px;
    underexposed_frac = sum(green(:) < 30)  / total_px;

    % ── 3. Field of View ─────────────────────────────────────────────────────
    gray_uint8 = uint8(green);
    min_r = round(min(H,W) * 0.25);
    max_r = round(min(H,W) * 0.65);
    fov_detected = false;
    fov_coverage = 0;

    try
        % imfindcircles: Computer Vision Toolbox
        [centers, radii, ~] = imfindcircles(gray_uint8, [min_r max_r], ...
            'ObjectPolarity','bright', 'Sensitivity', 0.92, 'Method','TwoStage');
        if ~isempty(radii)
            [~, idx] = max(radii);
            cx = centers(idx,1); cy = centers(idx,2); r = radii(idx);
            [X, Y] = meshgrid(1:W, 1:H);
            circle_mask = ((X-cx).^2 + (Y-cy).^2) <= r^2;
            fov_coverage = sum(circle_mask(:)) / total_px;
            fov_detected = true;
        else
            % Fallback: estimate from non-black region
            non_black = gray_uint8 > 15;
            fov_coverage = sum(non_black(:)) / total_px;
        end
    catch
        non_black = gray_uint8 > 15;
        fov_coverage = sum(non_black(:)) / total_px;
    end

    % ── Decision Logic ───────────────────────────────────────────────────────
    feedback = {};
    ungradable = {};
    borderline = {};

    % Focus checks
    if tenengrad < FOCUS_FAIL
        ungradable{end+1} = 'Image is severely blurred — hold camera steady and recapture.';
    elseif tenengrad < FOCUS_PASS
        borderline{end+1} = 'Image slightly out of focus — hold camera steadier for sharper capture.';
    end

    % Illumination checks
    if illum_mean < ILLUM_LOW
        if underexposed_frac > UNDEREXP_FRAC
            ungradable{end+1} = 'Insufficient illumination — improve retinal illumination before recapture.';
        else
            borderline{end+1} = 'Image appears dark — increase illumination if possible.';
        end
    elseif illum_mean > ILLUM_HIGH
        if overexposed_frac > OVEREXP_FRAC
            ungradable{end+1} = 'Excessive glare — adjust camera alignment to reduce reflection.';
        else
            borderline{end+1} = 'Image appears bright — reduce illumination or adjust angle.';
        end
    end

    % FOV checks
    if fov_coverage < FOV_FAIL
        ungradable{end+1} = 'Retina not fully visible — reposition the camera over the pupil.';
    elseif fov_coverage < FOV_PASS
        borderline{end+1} = 'Partial retinal field visible — centre the camera for better coverage.';
    end

    if ~isempty(ungradable)
        decision = 'QUALITY_UNGRADABLE';
        feedback = ungradable;
    elseif ~isempty(borderline)
        decision = 'QUALITY_BORDERLINE';
        feedback = borderline;
    else
        decision = 'QUALITY_GOOD';
        feedback = {'Image quality acceptable for grading.'};
    end

    % ── Build result struct ──────────────────────────────────────────────────
    result.focus_score      = tenengrad;
    result.laplacian_var    = laplacian_var;
    result.illum_mean       = illum_mean;
    result.overexposed_frac = overexposed_frac;
    result.underexposed_frac = underexposed_frac;
    result.fov_coverage     = fov_coverage;
    result.fov_detected     = fov_detected;
    result.decision         = decision;
    result.feedback         = feedback;
    result.validated        = false;
    result.disclaimer       = 'Thresholds not validated on clinical quality dataset.';

end
