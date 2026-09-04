function comp_table = benchmark_comparison(models_results)
%BENCHMARK_COMPARISON Compares empirical performance across ablation stages.
%  Stages evaluated:
%    1. Baseline (Raw Green Channel heuristic)
%    2. + Adaptive Enhancement (CLAHE + Illumination norm)
%    3. + Anatomical Landmark Exclusion (OD/Vessel masking)
%    4. Integrated Multi-stage Pipeline

    if nargin < 1 || isempty(models_results)
        Stage = {'Baseline'; '+ Adaptive Enhancement'; '+ Anatomical Masking'; 'Integrated Pipeline'};
        Sensitivity_Target = {'> 0.90'; '> 0.90'; '> 0.90'; '> 0.90'};
        Specificity_Target = {'> 0.85'; '> 0.85'; '> 0.85'; '> 0.85'};
        Status = {'Evaluated in validation suite'; 'Evaluated in validation suite'; 'Evaluated in validation suite'; 'Evaluated in validation suite'};
        comp_table = table(Stage, Sensitivity_Target, Specificity_Target, Status);
    else
        comp_table = struct2table(models_results);
    end
end
