function explain_result = explainability(img, grade_res, lesion_res, od_res, fov_res, vessel_res, output_dir)
%EXPLAINABILITY Generates clinical narrative, lesion overlay figure, and Grad-CAM map.
    addpath(fullfile(fileparts(mfilename('fullpath')), '..', 'explainability'));

    narrative = lesion_evidence(lesion_res, grade_res);
    annotated_img = annotated_output(img, od_res, fov_res, vessel_res, lesion_res);

    annotated_path = fullfile(output_dir, 'annotated_fundus.png');
    imwrite(annotated_img, annotated_path);

    explain_result.narrative = narrative;
    explain_result.annotated_image_path = annotated_path;
    explain_result.annotated_image = annotated_img;
    explain_result.gradcam_map = [];  % DL model required for GradCAM
end
