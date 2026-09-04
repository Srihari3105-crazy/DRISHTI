function [is_blurry, blur_metric] = blur_detection(img, threshold)
%BLUR_DETECTION Assesses whether image suffers from camera motion or defocus blur.
%  Default threshold is 60.0 on Laplacian variance.

    if nargin < 2
        threshold = 60.0;
    end

    if size(img, 3) == 3
        green = double(img(:,:,2));
    else
        green = double(img);
    end

    lap_filter = fspecial('laplacian', 0);
    lap_img = imfilter(green, lap_filter, 'replicate');
    blur_metric = var(lap_img(:));

    is_blurry = blur_metric < threshold;
end
