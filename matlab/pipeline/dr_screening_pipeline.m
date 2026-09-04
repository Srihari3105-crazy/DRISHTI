function result = dr_screening_pipeline(image_path, output_dir)
%DR_SCREENING_PIPELINE  Full DRISHTI-LENS retinal analysis pipeline.
%
%  RESULT = DR_SCREENING_PIPELINE(IMAGE_PATH, OUTPUT_DIR)
%
%  Orchestrates the complete DR screening pipeline:
%    1. Image Quality Assessment
%    2. Adaptive Enhancement (if borderline)
%    3. Retinal Structure Segmentation
%    4. Lesion Detection
%    5. ICDR DR Grading
%    6. Grad-CAM Explainability
%    7. Clinical Report Generation
%
%  Inputs:
%    image_path  - Full path to fundus image (JPEG or PNG)
%    output_dir  - Directory to save outputs (default: pwd/output)
%
%  Output:
%    result      - Struct with all pipeline outputs
%
%  Required MATLAB Toolboxes:
%    Image Processing Toolbox        - CLAHE, morphology, filtering
%    Computer Vision Toolbox         - Feature analysis, Hough transform
%    Statistics and ML Toolbox       - ROC, calibration (validation only)
%    Deep Learning Toolbox           - GradCAM (if DL model available)
%
%  DISCLAIMER:
%    This is an engineering prototype for SIH 2026 demonstration.
%    All outputs carry validated=false until benchmarked against clinical GT.
%    No clinical decisions should be made from these outputs without
%    ophthalmologist review.
%
%  Authors: Team DRISHTI-LENS, Smart India Hackathon 2026

    if nargin < 2
        output_dir = fullfile(pwd, 'output');
    end
    if ~exist(output_dir, 'dir')
        mkdir(output_dir);
    end

    fprintf('=== DRISHTI-LENS DR Screening Pipeline ===\n');
    fprintf('Image: %s\n', image_path);
    t_start = tic;

    % --- Load image ---
    if ~exist(image_path, 'file')
        error('Image file not found: %s', image_path);
    end
    try
        img = imread(image_path);
    catch e
        error('Failed to read image: %s', e.message);
    end
    if size(img, 3) == 1
        img = repmat(img, [1 1 3]);  % grayscale → RGB
    end
    img = im2uint8(img);

    fprintf('[1/7] Quality Assessment...\n');
    quality = image_quality_assessment(img);
    fprintf('      Decision: %s\n', quality.decision);

    % --- Enhancement if borderline ---
    if strcmp(quality.decision, 'QUALITY_BORDERLINE')
        fprintf('[2/7] Applying adaptive enhancement...\n');
        img_work = adaptive_enhancement(img, output_dir);
        quality_after = image_quality_assessment(img_work);
        fprintf('      Quality after enhancement: %s\n', quality_after.decision);
        enhancement_applied = true;
    else
        img_work = img;
        quality_after = quality;
        enhancement_applied = false;
    end

    % --- Reject ungradable ---
    if strcmp(quality_after.decision, 'QUALITY_UNGRADABLE')
        fprintf('[!] Image UNGRADABLE — pipeline halted.\n');
        fprintf('    Feedback: %s\n', strjoin(quality_after.feedback, '; '));
        result.status = 'UNGRADABLE';
        result.quality = quality_after;
        result.feedback = quality_after.feedback;
        result.processing_time_s = toc(t_start);
        return;
    end

    fprintf('[3/7] Optic Disc & Fovea Localisation...\n');
    od_result   = optic_disc_localization(img_work);
    fov_result  = fovea_localization(img_work, od_result);

    fprintf('[4/7] Vessel Segmentation & Lesion Detection...\n');
    vessel_result = vessel_segmentation(img_work);
    lesion_result = lesion_detection(img_work, od_result, vessel_result);

    fprintf('[5/7] ICDR DR Grading...\n');
    grading_result = dr_grading(img_work, lesion_result);
    fprintf('      Severity: %s (Level %d) | Referable: %d\n', ...
        grading_result.severity_name, grading_result.severity_level, ...
        grading_result.referable);

    fprintf('[6/7] Explainability...\n');
    explain_result = explainability(img_work, grading_result, lesion_result, ...
                                    od_result, fov_result, vessel_result, output_dir);

    fprintf('[7/7] Report Generation...\n');
    report_path = generate_report(image_path, quality_after, enhancement_applied, ...
                                  grading_result, lesion_result, od_result, ...
                                  vessel_result, explain_result, output_dir);
    fprintf('      Report: %s\n', report_path);

    t_total = toc(t_start);
    fprintf('=== Pipeline complete in %.2f seconds ===\n', t_total);

    % --- Build result struct ---
    result.status           = 'COMPLETED';
    result.quality          = quality_after;
    result.enhancement_applied = enhancement_applied;
    result.optic_disc       = od_result;
    result.fovea            = fov_result;
    result.vessels          = vessel_result;
    result.lesions          = lesion_result;
    result.grading          = grading_result;
    result.explainability   = explain_result;
    result.report_path      = report_path;
    result.processing_time_s = t_total;
    result.validated        = false;
    result.disclaimer       = ['AI-ASSISTED SCREENING PROTOTYPE. ' ...
        'Not clinically validated. Ophthalmologist review required.'];

end
