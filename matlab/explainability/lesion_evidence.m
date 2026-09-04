function narrative = lesion_evidence(lesions, grade)
%LESION_EVIDENCE Generates human-readable clinical explanation matching ICDR rules.

    lines = {};
    lines{end+1} = sprintf('Diagnostic Assessment: %s (ICDR Level %d)', grade.severity_name, grade.severity_level);
    lines{end+1} = sprintf('- Microaneurysms detected: %d candidates', lesions.microaneurysms.count);
    lines{end+1} = sprintf('- Hard Exudates detected: %d regions', lesions.exudates.count);
    lines{end+1} = sprintf('- Intraretinal Hemorrhages: %d candidates', lesions.hemorrhages.count);
    lines{end+1} = sprintf('- Neovascular proliferation: %d candidates', lesions.neovascularization.count);

    if grade.referable
        lines{end+1} = 'CLINICAL ACTION: Referable Diabetic Retinopathy detected. Secondary ophthalmologist review required.';
    else
        lines{end+1} = 'CLINICAL ACTION: Non-referable findings. Routine annual surveillance recommended.';
    end

    narrative = strjoin(lines, newline);
end
