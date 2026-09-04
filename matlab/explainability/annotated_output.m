function annotated_img = annotated_output(img, od_res, fov_res, vessel_res, lesion_res)
%ANNOTATED_OUTPUT Overlays segmented anatomical landmarks and lesions onto fundus image.

    annotated_img = img;
    [H, W, ~] = size(img);

    % Overlay vessels in cyan (30% alpha)
    if ~isempty(vessel_res.mask)
        v_mask = vessel_res.mask;
        cyan_overlay = annotated_img;
        cyan_overlay(:,:,1) = uint8(double(cyan_overlay(:,:,1)) .* (~v_mask) + double(v_mask) * 0);
        cyan_overlay(:,:,2) = uint8(double(cyan_overlay(:,:,2)) .* (~v_mask) + double(v_mask) * 200);
        cyan_overlay(:,:,3) = uint8(double(cyan_overlay(:,:,3)) .* (~v_mask) + double(v_mask) * 255);
        annotated_img = uint8(0.7 * double(annotated_img) + 0.3 * double(cyan_overlay));
    end

    % Overlay hemorrhages in red
    if ~isempty(lesion_res.hemorrhages.mask)
        he_mask = lesion_res.hemorrhages.mask;
        for c = 1:3
            ch = annotated_img(:,:,c);
            if c == 1
                ch(he_mask) = 255;
            else
                ch(he_mask) = 40;
            end
            annotated_img(:,:,c) = ch;
        end
    end

    % Overlay exudates in yellow
    if ~isempty(lesion_res.exudates.mask)
        ex_mask = lesion_res.exudates.mask;
        for c = 1:3
            ch = annotated_img(:,:,c);
            if c == 3
                ch(ex_mask) = 0;
            else
                ch(ex_mask) = 255;
            end
            annotated_img(:,:,c) = ch;
        end
    end

    % Draw Optic Disc boundary in green
    if ~isempty(od_res.center_xy) && od_res.radius_px > 0
        cx = od_res.center_xy(1); cy = od_res.center_xy(2); r = od_res.radius_px;
        theta = linspace(0, 2*pi, 200);
        xs = round(cx + r * cos(theta));
        ys = round(cy + r * sin(theta));
        valid = xs >= 1 & xs <= W & ys >= 1 & ys <= H;
        for i = find(valid)
            annotated_img(ys(i), xs(i), 1) = 0;
            annotated_img(ys(i), xs(i), 2) = 255;
            annotated_img(ys(i), xs(i), 3) = 0;
        end
    end

    % Draw Fovea landmark in bright amber
    if ~isempty(fov_res.center_xy)
        fx = fov_res.center_xy(1); fy = fov_res.center_xy(2);
        for dy = -4:4
            for dx = -4:4
                if (dx^2 + dy^2) <= 16 && (fy+dy >= 1) && (fy+dy <= H) && (fx+dx >= 1) && (fx+dx <= W)
                    annotated_img(fy+dy, fx+dx, 1) = 255;
                    annotated_img(fy+dy, fx+dx, 2) = 180;
                    annotated_img(fy+dy, fx+dx, 3) = 20;
                end
            end
        end
    end
end
