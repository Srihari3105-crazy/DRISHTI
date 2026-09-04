function img_norm = illumination_normalization(img, sigma)
%ILLUMINATION_NORMALIZATION Corrects uneven retinal vignetting via Gaussian background division.
%  Input:  img - uint8 RGB image
%          sigma - standard deviation of Gaussian kernel (default 60)

    if nargin < 2 || isempty(sigma), sigma = 60; end

    img_f = double(img) + 1.0;
    background = imgaussfilt(img_f, sigma);
    global_mean = mean(img_f(:));

    img_norm = (img_f ./ background) * global_mean;
    img_norm = uint8(min(max(img_norm, 0), 255));
end
