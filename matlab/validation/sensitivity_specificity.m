function [sens, spec, prec, f1] = sensitivity_specificity(y_true, y_pred)
%SENSITIVITY_SPECIFICITY Computes standard diagnostic accuracy metrics.
%  Input:  y_true - binary ground truth (1 = positive / referable, 0 = negative)
%          y_pred - binary predictions

    y_true = logical(y_true);
    y_pred = logical(y_pred);

    TP = sum(y_pred & y_true);
    FP = sum(y_pred & ~y_true);
    FN = sum(~y_pred & y_true);
    TN = sum(~y_pred & ~y_true);

    sens = TP / max(TP + FN, 1);
    spec = TN / max(TN + FP, 1);
    prec = TP / max(TP + FP, 1);
    f1   = 2 * prec * sens / max(prec + sens, 1e-9);
end
