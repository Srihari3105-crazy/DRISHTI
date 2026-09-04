function vessel_result = vessels(img)
%VESSELS Segments retinal vasculature using morphological bottom-hat on green channel.
%  Output struct:
%    mask            - binary mask of blood vessels
%    probability_map - continuous filter response [0, 1]

    green = img(:,:,2);
    clahe_green = adapthisteq(green, 'ClipLimit', 0.02, 'NumTiles', [8 8]);

    % Bottom-hat (black top-hat) extracts darker thin structures
    se = strel('disk', 6);
    bothat = imbothat(clahe_green, se);

    % Otsu threshold
    level = graythresh(bothat);
    vessel_bin = imbinarize(bothat, level);

    % Filter out small spurious noise
    vessel_clean = bwareaopen(vessel_bin, 25);

    vessel_result.mask = vessel_clean;
    vessel_result.probability_map = double(bothat) / 255.0;
end
