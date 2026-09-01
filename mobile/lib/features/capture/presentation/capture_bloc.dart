import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:equatable/equatable.dart';
import 'dart:math';

// Events
abstract class CaptureEvent extends Equatable {
  @override
  List<Object?> get props => [];
}

class CaptureStarted extends CaptureEvent {
  final String patientId;
  final String eye; // OD or OS
  CaptureStarted(this.patientId, this.eye);
}

class QualityFrameProcessed extends CaptureEvent {
  final double score;
  final List<String> defects;
  QualityFrameProcessed(this.score, this.defects);
}

class ImageCaptured extends CaptureEvent {}

class GradingCompleted extends CaptureEvent {
  final Map<String, dynamic> result;
  GradingCompleted(this.result);
}

class CaptureReset extends CaptureEvent {}

// States
abstract class CaptureState extends Equatable {
  @override
  List<Object?> get props => [];
}

class CaptureInitial extends CaptureState {}

class CapturePreview extends CaptureState {
  final double qualityScore;
  final List<String> defects;
  final bool isQualityPassing;
  final int consecutivePassCount;

  CapturePreview({
    required this.qualityScore,
    required this.defects,
    required this.isQualityPassing,
    required this.consecutivePassCount,
  });

  @override
  List<Object?> get props => [qualityScore, defects, isQualityPassing, consecutivePassCount];
}

class CaptureProcessing extends CaptureState {
  final String message;
  CaptureProcessing(this.message);
}

class CaptureComplete extends CaptureState {
  final Map<String, dynamic> gradingResult;
  CaptureComplete(this.gradingResult);
}

class CaptureError extends CaptureState {
  final String message;
  CaptureError(this.message);
}

// Bloc
class CaptureBloc extends Bloc<CaptureEvent, CaptureState> {
  int _consecutivePassCount = 0;
  String _currentPatientId = '';
  String _currentEye = 'OD';

  CaptureBloc() : super(CaptureInitial()) {
    on<CaptureStarted>(_onStarted);
    on<QualityFrameProcessed>(_onQualityFrame);
    on<ImageCaptured>(_onImageCaptured);
    on<GradingCompleted>(_onGradingCompleted);
    on<CaptureReset>(_onReset);
  }

  void _onStarted(CaptureStarted event, Emitter<CaptureState> emit) {
    _currentPatientId = event.patientId;
    _currentEye = event.eye;
    _consecutivePassCount = 0;
    emit(CapturePreview(
      qualityScore: 0.0,
      defects: [],
      isQualityPassing: false,
      consecutivePassCount: 0,
    ));
  }

  void _onQualityFrame(QualityFrameProcessed event, Emitter<CaptureState> emit) {
    if (event.score >= 0.85) {
      _consecutivePassCount++;
    } else {
      _consecutivePassCount = 0;
    }

    emit(CapturePreview(
      qualityScore: event.score,
      defects: event.defects,
      isQualityPassing: event.score >= 0.85,
      consecutivePassCount: _consecutivePassCount,
    ));

    // Auto-capture after 3 consecutive passing frames
    if (_consecutivePassCount >= 3) {
      add(ImageCaptured());
    }
  }

  Future<void> _onImageCaptured(ImageCaptured event, Emitter<CaptureState> emit) async {
    emit(CaptureProcessing('Running AI grading...'));

    // Mock grading result (replace with real ONNX inference)
    await Future.delayed(const Duration(milliseconds: 1200));

    final random = Random();
    final severity = random.nextInt(5);
    final efs = 0.65 + random.nextDouble() * 0.30;
    final dme = severity >= 2 ? random.nextDouble() * 0.8 : random.nextDouble() * 0.2;

    final mockResult = {
      'patient_id': _currentPatientId,
      'eye': _currentEye,
      'image_hash': List.generate(64, (_) => random.nextInt(16).toRadixString(16)).join(),
      'quality_score': 0.92,
      'quality_defects': <String>[],
      'severity_level': severity,
      'dme_risk': dme,
      'efs_score': efs,
      'lesion_masks_rle': _getMockLesions(severity),
      'rule_trace': _getMockRuleTrace(severity),
      'captured_at': DateTime.now().toIso8601String(),
    };

    add(GradingCompleted(mockResult));
  }

  void _onGradingCompleted(GradingCompleted event, Emitter<CaptureState> emit) {
    emit(CaptureComplete(event.result));
  }

  void _onReset(CaptureReset event, Emitter<CaptureState> emit) {
    _consecutivePassCount = 0;
    emit(CaptureInitial());
  }

  Map<String, String> _getMockLesions(int severity) {
    if (severity == 0) return {};
    if (severity == 1) return {'MA': '10 5 20 3'};
    if (severity == 2) return {'MA': '10 5', 'HE': '100 10', 'EX': '150 6'};
    if (severity == 3) return {'MA': '10 5', 'HE': '100 15', 'EX': '150 8', 'CWS': '300 5', 'IRMA': '400 3'};
    return {'MA': '10 5', 'HE': '100 20', 'EX': '150 10', 'CWS': '300 8', 'VB': '350 5', 'IRMA': '400 4', 'NV': '500 10'};
  }

  List<Map<String, dynamic>> _getMockRuleTrace(int severity) {
    if (severity == 0) return [{'rule_id': 'ICDR-0', 'met': true, 'description': 'No abnormalities detected', 'zones': []}];
    if (severity == 1) return [
      {'rule_id': 'ICDR-1.1', 'met': true, 'description': 'Microaneurysms only', 'zones': ['zone_1']},
    ];
    if (severity >= 2 && severity <= 3) return [
      {'rule_id': 'ICDR-2.1', 'met': true, 'description': 'More than just microaneurysms', 'zones': ['zone_1', 'zone_2']},
      {'rule_id': 'ICDR-2.2', 'met': true, 'description': 'Hard exudates present', 'zones': ['zone_2']},
      {'rule_id': 'ICDR-3.1', 'met': severity >= 3, 'description': 'Venous beading in 2+ quadrants', 'zones': severity >= 3 ? ['zone_1', 'zone_3'] : []},
    ];
    return [
      {'rule_id': 'ICDR-4.1', 'met': true, 'description': 'Neovascularization detected', 'zones': ['zone_1', 'zone_2']},
      {'rule_id': 'ICDR-4.2', 'met': true, 'description': 'Vitreous/preretinal hemorrhage', 'zones': ['zone_1']},
    ];
  }
}
