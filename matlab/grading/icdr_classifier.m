function result = icdr_classifier(img, lesion_result)
%ICDR_CLASSIFIER  Map lesion counts to ICDR severity (rule-based prototype).
%
%  RESULT = ICDR_CLASSIFIER(IMG, LESION_RESULT)
%
%  Implements ICDR grading criteria:
%    Level 0: No DR         — no lesions
%    Level 1: Mild NPDR     — microaneurysms only
%    Level 2: Moderate NPDR — more than MAs, less than severe
%    Level 3: Severe NPDR   — approximation of 4-2-1 rule
%    Level 4: PDR           — neovascularization present
%
%  Reference:
%    Wilkinson et al., "Proposed International Clinical Diabetic Retinopathy
%    and Diabetic Macular Edema Disease Severity Scales,"
%    Ophthalmology 110(9):1677-1682, 2003.
%
%  DISCLAIMER:
%    This is a rule-based prototype. Classification accuracy has NOT been
%    measured against a ground-truth dataset. Results must be verified by
%    an ophthalmologist. Sensitivity and specificity are UNKNOWN until
%    matlab/validation/evaluate_model.m is run with a labelled dataset.

    labels = {'No DR', 'Mild NPDR', 'Moderate NPDR', 'Severe NPDR', 'Proliferative DR'};

    ma_count = lesion_result.microaneurysms.count;
    ex_count = lesion_result.exudates.count;
    he_count = lesion_result.hemorrhages.count;
    nv_count = lesion_result.neovascularization.count;

    rule_trace = {};

    % Level 4: PDR
    if nv_count > 0
        level = 4;
        rule_trace{end+1} = struct('rule_id','ICDR-4.1','met',true, ...
            'desc',sprintf('Neovascularization candidates: %d', nv_count));
        confidence = min(0.85, lesion_result.neovascularization.confidence * 1.2);
        dme_risk = min(0.95, 0.4 + ex_count/20);

    % Level 3: Severe NPDR
    elseif he_count >= 10 || (he_count >= 5 && ex_count >= 5)
        level = 3;
        rule_trace{end+1} = struct('rule_id','ICDR-3.1','met',true, ...
            'desc',sprintf('Extensive hemorrhages (%d candidates)', he_count));
        confidence = min(0.75, 0.45 + he_count/30);
        dme_risk = min(0.85, 0.3 + ex_count/25);

    % Level 2: Moderate NPDR
    elseif (ma_count >= 3 && (ex_count >= 2 || he_count >= 2)) || he_count >= 3
        level = 2;
        rule_trace{end+1} = struct('rule_id','ICDR-2.1','met',true, ...
            'desc','More than microaneurysms only');
        confidence = min(0.70, 0.40 + ma_count/20 + ex_count/15);
        dme_risk = min(0.65, 0.2 + ex_count/20);

    % Level 1: Mild NPDR
    elseif ma_count >= 1
        level = 1;
        rule_trace{end+1} = struct('rule_id','ICDR-1.1','met',true, ...
            'desc',sprintf('Microaneurysm candidates only (%d)', ma_count));
        confidence = min(0.60, 0.35 + ma_count/15);
        dme_risk = min(0.25, 0.05 + ma_count/30);

    % Level 0: No DR
    else
        level = 0;
        rule_trace{end+1} = struct('rule_id','ICDR-0','met',true, ...
            'desc','No lesion candidates detected');
        confidence = min(0.75, 0.50 + (5-ma_count)/10);
        dme_risk = 0.05;
    end

    efs_score = max(0.05, 1 - (ma_count/30 + ex_count/25 + he_count/20 + nv_count*0.3));

    result.severity_level = level;
    result.severity_name  = labels{level+1};
    result.referable      = level >= 2;
    result.confidence     = confidence;
    result.calibrated_confidence = [];  % empty until calibration is run
    result.dme_risk       = dme_risk;
    result.efs_score      = efs_score;
    result.rule_trace     = rule_trace;
    result.method         = 'rule_based_ICDR_lesion_count';
    result.validated      = false;
    result.disclaimer     = ['Rule-based prototype. Sensitivity/specificity UNKNOWN. ' ...
        'Run matlab/validation/evaluate_model.m with labelled dataset.'];

end
