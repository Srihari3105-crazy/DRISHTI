function [decision, feedback] = gradability_decision(focus_val, mean_illum, overexp, underexp, fov_cov)
%GRADABILITY_DECISION Combines individual quality scores into a triage decision.
%  Returns decision: 'QUALITY_GOOD' | 'QUALITY_BORDERLINE' | 'QUALITY_UNGRADABLE'

    FOCUS_FAIL  = 60;
    FOCUS_PASS  = 150;
    ILLUM_LOW   = 60;
    ILLUM_HIGH  = 210;
    OVEREXP_MAX = 0.10;
    UNDEREXP_MAX= 0.20;
    FOV_FAIL    = 0.35;
    FOV_PASS    = 0.55;

    ungradable = {};
    borderline = {};

    if focus_val < FOCUS_FAIL
        ungradable{end+1} = 'Severe blur detected — camera motion or defocus.';
    elseif focus_val < FOCUS_PASS
        borderline{end+1} = 'Slight blur detected — stabilize hand and camera.';
    end

    if mean_illum < ILLUM_LOW
        if underexp > UNDEREXP_MAX
            ungradable{end+1} = 'Severe underexposure — illumination too dark.';
        else
            borderline{end+1} = 'Moderate underexposure.';
        end
    elseif mean_illum > ILLUM_HIGH
        if overexp > OVEREXP_MAX
            ungradable{end+1} = 'Excessive glare/overexposure — specular reflection.';
        else
            borderline{end+1} = 'Moderate overexposure.';
        end
    end

    if fov_cov < FOV_FAIL
        ungradable{end+1} = 'Incomplete retinal field of view (<35%).';
    elseif fov_cov < FOV_PASS
        borderline{end+1} = 'Marginal field of view (<55%).';
    end

    if ~isempty(ungradable)
        decision = 'QUALITY_UNGRADABLE';
        feedback = ungradable;
    elseif ~isempty(borderline)
        decision = 'QUALITY_BORDERLINE';
        feedback = borderline;
    else
        decision = 'QUALITY_GOOD';
        feedback = {'Image quality passed all screening criteria.'};
    end
end
