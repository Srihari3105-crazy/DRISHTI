function report_path = generate_report(image_path, quality, enhancement_applied, grading, lesions, od_result, vessel_result, explain_result, output_dir)
%GENERATE_REPORT Produces a structured plain-text and HTML clinical report.

    [~, fname, ~] = fileparts(image_path);
    report_path = fullfile(output_dir, sprintf('%s_clinical_report.txt', fname));

    fid = fopen(report_path, 'w');
    if fid == -1
        warning('Could not open report file for writing: %s', report_path);
        return;
    end

    fprintf(fid, '======================================================================\n');
    fprintf(fid, 'DRISHTI-LENS — CLINICAL SCREENING REPORT\n');
    fprintf(fid, '======================================================================\n');
    fprintf(fid, 'DISCLAIMER: AI-ASSISTED SCREENING PROTOTYPE.\n');
    fprintf(fid, 'NOT CLINICALLY VALIDATED. OPHTHALMOLOGIST REVIEW REQUIRED.\n\n');

    fprintf(fid, 'Source Image: %s\n', image_path);
    fprintf(fid, 'Screening Timestamp: %s\n\n', datestr(now));

    fprintf(fid, '[1] QUALITY ASSESSMENT\n');
    fprintf(fid, '    Decision:           %s\n', quality.decision);
    fprintf(fid, '    Focus Score:        %.2f\n', quality.focus_score);
    fprintf(fid, '    Mean Illumination:  %.2f / 255\n', quality.illum_mean);
    fprintf(fid, '    FOV Coverage:       %.2f%%\n', quality.fov_coverage * 100);
    fprintf(fid, '    Enhancement Needed: %d\n\n', enhancement_applied);

    fprintf(fid, '[2] DIAGNOSTIC GRADING\n');
    fprintf(fid, '    ICDR Severity:      %s (Level %d)\n', grading.severity_name, grading.severity_level);
    fprintf(fid, '    Referable Status:   %s\n', char(string(grading.referable)));
    fprintf(fid, '    Confidence Score:   %.4f (Uncalibrated)\n', grading.confidence);
    fprintf(fid, '    DME Risk Indicator: %.2f%%\n', grading.dme_risk * 100);
    fprintf(fid, '    EFS Score:          %.4f\n\n', grading.efs_score);

    fprintf(fid, '[3] RETINAL LESION FINDINGS\n');
    fprintf(fid, '    Microaneurysms:     %d candidates\n', lesions.microaneurysms.count);
    fprintf(fid, '    Hard Exudates:      %d regions\n', lesions.exudates.count);
    fprintf(fid, '    Hemorrhages:        %d candidates\n', lesions.hemorrhages.count);
    fprintf(fid, '    Neovascularization: %d proliferation zones\n\n', lesions.neovascularization.count);

    fprintf(fid, '[4] EXPLAINABILITY NARRATIVE\n');
    fprintf(fid, '%s\n\n', explain_result.narrative);

    fprintf(fid, '[5] OUTPUT ARTIFACTS\n');
    fprintf(fid, '    Annotated Fundus:   %s\n', explain_result.annotated_image_path);
    fprintf(fid, '======================================================================\n');

    fclose(fid);
end
