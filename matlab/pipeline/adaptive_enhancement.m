function img_out = adaptive_enhancement(img, output_dir)
%ADAPTIVE_ENHANCEMENT  CLAHE + illumination normalization + NLM denoising.
%  Uses Image Processing Toolbox: adapthisteq, imgaussfilt, medfilt2
%  Uses Computer Vision Toolbox: imbilatfilt (bilateral filter)

    if nargin < 2, output_dir = []; end

    % Step 1: CLAHE on L channel of LAB colour space
    lab = rgb2lab(img);
    L = lab(:,:,1) / 100;  % Normalize L to [0,1]
    L_eq = adapthisteq(L, 'ClipLimit', 0.02, 'NumTiles', [8 8]);
    lab(:,:,1) = L_eq * 100;
    img_clahe = uint8(lab2rgb(lab) * 255);

    if ~isempty(output_dir)
        imwrite(img_clahe, fullfile(output_dir, 'step1_clahe.jpg'));
    end

    % Step 2: Illumination normalization (divide by Gaussian background)
    img_f = double(img_clahe) + 1;
    sigma = 60;
    background = imgaussfilt(img_f, sigma);
    global_mean = mean(img_f(:));
    img_norm = (img_f ./ background) * global_mean;
    img_norm = uint8(min(max(img_norm, 0), 255));

    if ~isempty(output_dir)
        imwrite(img_norm, fullfile(output_dir, 'step2_illum_norm.jpg'));
    end

    % Step 3: Edge-preserving denoising (bilateral filter, CV Toolbox)
    try
        img_denoised = imbilatfilt(img_norm, 10, 5);
    catch
        % Fallback to median filter if CV Toolbox unavailable
        img_denoised = img_norm;
        for c = 1:3
            img_denoised(:,:,c) = medfilt2(img_norm(:,:,c), [3 3]);
        end
    end

    if ~isempty(output_dir)
        imwrite(img_denoised, fullfile(output_dir, 'step3_denoised.jpg'));
    end

    img_out = img_denoised;

end
