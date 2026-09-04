function cam_map = gradcam(net, img, target_class)
%GRADCAM Computes Gradient-weighted Class Activation Mapping (Grad-CAM).
%  Requires: Deep Learning Toolbox (gradCAM)

    try
        [H, W, ~] = size(img);
        img_resized = imresize(img, [512 512]);
        % Deep learning toolbox gradCAM API
        cam_map_raw = gradCAM(net, img_resized, target_class);
        cam_map = imresize(cam_map_raw, [H, W]);
    catch e
        warning('Grad-CAM requires pre-trained SeriesNetwork or DAGNetwork: %s', e.message);
        cam_map = [];
    end
end
