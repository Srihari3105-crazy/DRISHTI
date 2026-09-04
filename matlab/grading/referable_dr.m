function is_referable = referable_dr(severity_level, dme_risk)
%REFERABLE_DR Implements the clinical standard definition of referable DR.
%  Referable if ICDR level >= 2 (Moderate NPDR or worse) OR DME risk > 0.30.

    if nargin < 2 || isempty(dme_risk)
        dme_risk = 0.0;
    end

    is_referable = (severity_level >= 2) || (dme_risk >= 0.30);
end
