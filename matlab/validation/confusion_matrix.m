function cm = confusion_matrix(y_true, y_pred, class_labels)
%CONFUSION_MATRIX Computes and renders a confusion chart across diagnostic classes.
%  Requires: Deep Learning Toolbox or Statistics and ML Toolbox

    if nargin < 3 || isempty(class_labels)
        class_labels = {'No DR', 'Mild', 'Moderate', 'Severe', 'PDR'};
    end

    try
        figure;
        chart = confusionchart(y_true, y_pred, 'ClassLabels', class_labels);
        chart.Title = 'Diabetic Retinopathy Diagnostic Agreement Matrix';
        cm = chart.NormalizedValues;
    catch
        cm = zeros(length(class_labels));
        for i = 1:length(y_true)
            r = y_true(i) + 1;
            c = y_pred(i) + 1;
            cm(r, c) = cm(r, c) + 1;
        end
    end
end
