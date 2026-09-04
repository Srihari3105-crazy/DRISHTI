function calibrated_prob = confidence_calibration(raw_prob, temperature)
%CONFIDENCE_CALIBRATION Applies learned temperature scaling to model confidence.
%  Input:  raw_prob - uncalibrated softmax probability [0, 1]
%          temperature - scalar T (fitted via NLL on validation set)
%  Output: calibrated_prob - scaled probability

    if nargin < 2 || isempty(temperature) || temperature <= 0
        temperature = 1.0;  % Identity scaling (uncalibrated)
    end

    raw_prob = max(1e-6, min(1 - 1e-6, raw_prob));
    logit = log(raw_prob / (1 - raw_prob));
    scaled_logit = logit / temperature;
    calibrated_prob = 1.0 / (1.0 + exp(-scaled_logit));
end
