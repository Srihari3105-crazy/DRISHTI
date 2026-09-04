function result = dr_grading(img, lesion_result)
%DR_GRADING  ICDR 0-4 classification from lesion evidence.
%  Rule-based prototype mapping lesion counts to ICDR criteria.
%  Deep learning model (EfficientNet-B4) is the production path.
%  See matlab/grading/icdr_classifier.m for detailed implementation.

    result = icdr_classifier(img, lesion_result);

end
