function [mean_illum, overexp_frac, underexp_frac] = illumination_score(img)
%ILLUMINATION_SCORE Assesses mean brightness and exposure extremes.
%  Input:  img - uint8 RGB or grayscale fundus image
%  Output: mean_illum    - mean pixel intensity on green channel [0-255]
%          overexp_frac  - fraction of saturated pixels (>250)
%          underexp_frac - fraction of dark pixels (<30)

    if size(img, 3) == 3
        green = double(img(:,:,2));
    else
        green = double(img);
    end

    total_px = numel(green);
    mean_illum = mean(green(:));
    overexp_frac = sum(green(:) > 250) / total_px;
    underexp_frac = sum(green(:) < 30) / total_px;
end
