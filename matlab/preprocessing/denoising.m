function img_denoised = denoising(img, filter_type)
%DENOISING Edge-preserving smoothing for fundus photography.
%  Input:  img - uint8 RGB image
%          filter_type - 'bilateral' (default) or 'median'

    if nargin < 2 || isempty(filter_type), filter_type = 'bilateral'; end

    if strcmp(filter_type, 'bilateral')
        try
            img_denoised = imbilatfilt(img, 10, 5);
            return;
        catch
            % fallback if CV toolbox unavailable
        end
    end

    img_denoised = img;
    for c = 1:size(img, 3)
        img_denoised(:,:,c) = medfilt2(img(:,:,c), [3 3]);
    end
end
