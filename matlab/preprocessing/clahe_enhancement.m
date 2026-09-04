function img_clahe = clahe_enhancement(img, clip_limit, num_tiles)
%CLAHE_ENHANCEMENT Contrast-Limited Adaptive Histogram Equalization on L-channel.
%  Input:  img - uint8 RGB image
%          clip_limit - scalar (default 0.02)
%          num_tiles - [rows cols] vector (default [8 8])
%  Requires: Image Processing Toolbox (rgb2lab, adapthisteq, lab2rgb)

    if nargin < 2 || isempty(clip_limit), clip_limit = 0.02; end
    if nargin < 3 || isempty(num_tiles),  num_tiles = [8 8]; end

    lab = rgb2lab(img);
    L = lab(:,:,1) / 100.0;
    L_eq = adapthisteq(L, 'ClipLimit', clip_limit, 'NumTiles', num_tiles);
    lab(:,:,1) = L_eq * 100.0;
    img_clahe = uint8(lab2rgb(lab) * 255);
end
