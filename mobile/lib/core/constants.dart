/// App-wide constants for DRISHTI-LENS
class AppConstants {
  static const String appName = 'DRISHTI-LENS';
  static const String appVersion = '1.0.0-mvp';

  // API
  static const String apiBaseUrl = 'http://192.168.1.100:8000/api/v1';  // Change to laptop IP

  // Quality Gate Thresholds
  static const double qualityPassThreshold = 0.85;
  static const int consecutivePassFrames = 3;
  static const Map<String, double> defectThresholds = {
    'defocus': 0.4,
    'glare': 0.35,
    'small_pupil': 0.5,
    'cataract': 0.45,
    'off_center': 0.3,
  };

  // Models
  static const String qualityGateModel = 'assets/models/quality_gate_v1.tflite';
  static const String gradingModel = 'assets/models/lesion_sev_v1.onnx';

  // Inference
  static const int qualityInputSize = 224;
  static const int gradingInputSize = 512;
  static const int qualityFps = 5;
  static const double inferenceTimeout = 5.0; // seconds

  // Sync
  static const int syncIntervalMinutes = 15;
  static const List<int> backoffMinutes = [1, 4, 15, 60, 360]; // exponential backoff

  // Severity labels
  static const Map<int, String> severityLabels = {
    0: 'No DR',
    1: 'Mild NPDR',
    2: 'Moderate NPDR',
    3: 'Severe NPDR',
    4: 'PDR',
  };

  // Lesion type labels
  static const Map<String, String> lesionLabels = {
    'MA': 'Microaneurysms',
    'HE': 'Hemorrhages',
    'EX': 'Exudates',
    'CWS': 'Cotton Wool Spots',
    'VB': 'Venous Beading',
    'IRMA': 'IRMA',
    'NV': 'Neovascularization',
  };
}
