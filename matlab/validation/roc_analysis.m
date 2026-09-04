function [auc, X, Y] = roc_analysis(y_true, y_score, plot_fig)
%ROC_ANALYSIS Computes empirical Receiver Operating Characteristic and AUC.
%  Requires: Statistics and Machine Learning Toolbox (perfcurve)

    if nargin < 3, plot_fig = false; end

    try
        [X, Y, ~, auc] = perfcurve(logical(y_true), y_score, true);
        if plot_fig
            figure;
            plot(X, Y, 'LineWidth', 2);
            hold on;
            plot([0 1], [0 1], 'k--');
            xlabel('False Positive Rate (1 - Specificity)');
            ylabel('True Positive Rate (Sensitivity)');
            title(sprintf('ROC Curve (AUC = %.4f)', auc));
            grid on;
        end
    catch e
        warning('perfcurve execution failed: %s', e.message);
        auc = NaN; X = []; Y = [];
    end
end
