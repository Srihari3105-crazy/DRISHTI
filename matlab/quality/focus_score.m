function score = focus_score(img)
%FOCUS_SCORE Computes Tenengrad gradient energy for retinal fundus sharpness.
%  Input:  img - uint8 RGB or grayscale fundus image
%  Output: score - float Tenengrad focus measure (higher indicates sharper focus)
%
%  Requires: Image Processing Toolbox (fspecial, imfilter)

    if size(img, 3) == 3
        green = double(img(:,:,2));
    else
        green = double(img);
    end

    sobel_h = fspecial('sobel');
    sobel_v = sobel_h';
    Gx = imfilter(green, sobel_h, 'replicate');
    Gy = imfilter(green, sobel_v, 'replicate');

    score = mean(Gx(:).^2 + Gy(:).^2);
end
