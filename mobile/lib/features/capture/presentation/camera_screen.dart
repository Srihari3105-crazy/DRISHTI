import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'dart:math';
import '../../../core/theme.dart';
import '../../../core/constants.dart';
import 'capture_bloc.dart';

class CameraScreen extends StatefulWidget {
  final String patientId;
  const CameraScreen({super.key, required this.patientId});

  @override
  State<CameraScreen> createState() => _CameraScreenState();
}

class _CameraScreenState extends State<CameraScreen> with TickerProviderStateMixin {
  String _selectedEye = 'OD';
  late AnimationController _pulseController;

  @override
  void initState() {
    super.initState();
    _pulseController = AnimationController(vsync: this, duration: const Duration(seconds: 2))..repeat();
    _startCapture();
    // Simulate quality gate updates
    _simulateQualityGate();
  }

  void _startCapture() {
    context.read<CaptureBloc>().add(CaptureStarted(widget.patientId, _selectedEye));
  }

  void _simulateQualityGate() async {
    final random = Random();
    while (mounted) {
      await Future.delayed(const Duration(milliseconds: 200)); // 5 fps
      if (!mounted) break;
      final state = context.read<CaptureBloc>().state;
      if (state is! CapturePreview) break;

      // Simulate improving quality over time
      final score = 0.6 + random.nextDouble() * 0.38;
      final defects = <String>[];
      if (score < 0.85) {
        final possibleDefects = ['defocus', 'glare', 'small_pupil', 'off_center'];
        defects.add(possibleDefects[random.nextInt(possibleDefects.length)]);
      }
      context.read<CaptureBloc>().add(QualityFrameProcessed(score, defects));
    }
  }

  @override
  Widget build(BuildContext context) {
    return BlocListener<CaptureBloc, CaptureState>(
      listener: (context, state) {
        if (state is CaptureComplete) {
          Navigator.of(context).pushReplacementNamed('/result/${state.gradingResult['patient_id']}');
          // For now just show result overlay
        }
      },
      child: Scaffold(
        backgroundColor: Colors.black,
        body: SafeArea(
          child: BlocBuilder<CaptureBloc, CaptureState>(
            builder: (context, state) {
              if (state is CaptureProcessing) {
                return _buildProcessingView(state.message);
              }
              if (state is CaptureComplete) {
                return _buildResultPreview(state.gradingResult);
              }
              return _buildCameraView(state);
            },
          ),
        ),
      ),
    );
  }

  Widget _buildCameraView(CaptureState state) {
    final qualityScore = state is CapturePreview ? state.qualityScore : 0.0;
    final defects = state is CapturePreview ? state.defects : <String>[];
    final isPassing = state is CapturePreview ? state.isQualityPassing : false;
    final consecutiveCount = state is CapturePreview ? state.consecutivePassCount : 0;

    return Stack(
      children: [
        // Camera preview placeholder (black with circle overlay)
        Container(
          color: Colors.black,
          child: Center(
            child: Container(
              width: 300,
              height: 300,
              decoration: BoxDecoration(
                shape: BoxShape.circle,
                border: Border.all(
                  color: isPassing ? AppTheme.success : AppTheme.danger,
                  width: 3,
                ),
                boxShadow: [
                  BoxShadow(
                    color: (isPassing ? AppTheme.success : AppTheme.danger).withOpacity(0.3),
                    blurRadius: 20,
                    spreadRadius: 5,
                  ),
                ],
              ),
              child: Center(
                child: Column(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    Icon(
                      Icons.camera_alt,
                      size: 48,
                      color: Colors.white.withOpacity(0.5),
                    ),
                    const SizedBox(height: 8),
                    Text(
                      'Point at fundus',
                      style: TextStyle(color: Colors.white.withOpacity(0.5), fontSize: 14),
                    ),
                  ],
                ),
              ),
            ),
          ),
        ),

        // Top bar - Eye selector & back
        Positioned(
          top: 10,
          left: 16,
          right: 16,
          child: Row(
            children: [
              IconButton(
                icon: const Icon(Icons.arrow_back, color: Colors.white),
                onPressed: () => Navigator.of(context).pop(),
              ),
              const Spacer(),
              // Eye selector
              Container(
                padding: const EdgeInsets.all(4),
                decoration: BoxDecoration(
                  color: Colors.black54,
                  borderRadius: BorderRadius.circular(12),
                ),
                child: Row(
                  children: [
                    _eyeButton('OD', 'Right'),
                    const SizedBox(width: 4),
                    _eyeButton('OS', 'Left'),
                  ],
                ),
              ),
            ],
          ),
        ),

        // Quality gate overlay
        Positioned(
          bottom: 0,
          left: 0,
          right: 0,
          child: Container(
            padding: const EdgeInsets.all(20),
            decoration: BoxDecoration(
              gradient: LinearGradient(
                begin: Alignment.bottomCenter,
                end: Alignment.topCenter,
                colors: [Colors.black.withOpacity(0.9), Colors.transparent],
              ),
            ),
            child: Column(
              children: [
                // Quality score bar
                Row(
                  children: [
                    Text(
                      isPassing ? 'GOOD' : 'RETAKE',
                      style: TextStyle(
                        color: isPassing ? AppTheme.success : AppTheme.danger,
                        fontWeight: FontWeight.w800,
                        fontSize: 16,
                        letterSpacing: 2,
                      ),
                    ),
                    const Spacer(),
                    Text(
                      '${(qualityScore * 100).toStringAsFixed(0)}%',
                      style: TextStyle(
                        color: isPassing ? AppTheme.success : AppTheme.danger,
                        fontWeight: FontWeight.w700,
                        fontSize: 24,
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 8),

                // Progress bar
                ClipRRect(
                  borderRadius: BorderRadius.circular(4),
                  child: LinearProgressIndicator(
                    value: qualityScore,
                    backgroundColor: Colors.white12,
                    color: isPassing ? AppTheme.success : AppTheme.danger,
                    minHeight: 6,
                  ),
                ),
                const SizedBox(height: 8),

                // Defects
                if (defects.isNotEmpty)
                  Text(
                    defects.map((d) => d.toUpperCase()).join(' · '),
                    style: const TextStyle(color: AppTheme.danger, fontSize: 12, fontWeight: FontWeight.w600, letterSpacing: 1),
                  ),

                // Auto-capture countdown
                if (consecutiveCount > 0 && consecutiveCount < 3)
                  Padding(
                    padding: const EdgeInsets.only(top: 8),
                    child: Text(
                      'Auto-capture in ${3 - consecutiveCount}...',
                      style: const TextStyle(color: AppTheme.success, fontSize: 14, fontWeight: FontWeight.w600),
                    ),
                  ),

                const SizedBox(height: 16),

                // Manual capture button
                GestureDetector(
                  onTap: () => context.read<CaptureBloc>().add(ImageCaptured()),
                  child: Container(
                    width: 72,
                    height: 72,
                    decoration: BoxDecoration(
                      shape: BoxShape.circle,
                      border: Border.all(color: Colors.white, width: 4),
                      color: isPassing ? AppTheme.success.withOpacity(0.3) : Colors.white12,
                    ),
                    child: const Icon(Icons.camera, color: Colors.white, size: 32),
                  ),
                ),
              ],
            ),
          ),
        ),
      ],
    );
  }

  Widget _eyeButton(String eye, String label) {
    final selected = _selectedEye == eye;
    return GestureDetector(
      onTap: () {
        setState(() => _selectedEye = eye);
        _startCapture();
      },
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
        decoration: BoxDecoration(
          color: selected ? AppTheme.primary : Colors.transparent,
          borderRadius: BorderRadius.circular(8),
        ),
        child: Text(
          '$eye ($label)',
          style: TextStyle(
            color: selected ? Colors.white : Colors.white70,
            fontWeight: selected ? FontWeight.w700 : FontWeight.w400,
            fontSize: 13,
          ),
        ),
      ),
    );
  }

  Widget _buildProcessingView(String message) {
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          const SizedBox(
            width: 64,
            height: 64,
            child: CircularProgressIndicator(strokeWidth: 3, color: AppTheme.primary),
          ),
          const SizedBox(height: 24),
          Text(message, style: const TextStyle(color: Colors.white, fontSize: 16, fontWeight: FontWeight.w600)),
          const SizedBox(height: 8),
          const Text('~1.2 seconds on device', style: TextStyle(color: AppTheme.textMuted, fontSize: 13)),
        ],
      ),
    );
  }

  Widget _buildResultPreview(Map<String, dynamic> result) {
    final severity = result['severity_level'] as int;
    final efs = result['efs_score'] as double;
    final severityLabel = AppConstants.severityLabels[severity] ?? 'Unknown';
    final severityColor = AppTheme.severityColors[severity] ?? AppTheme.textMuted;

    return SingleChildScrollView(
      padding: const EdgeInsets.all(20),
      child: Column(
        children: [
          const SizedBox(height: 20),
          // Severity badge
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 12),
            decoration: BoxDecoration(
              color: severityColor.withOpacity(0.15),
              borderRadius: BorderRadius.circular(16),
              border: Border.all(color: severityColor.withOpacity(0.3)),
            ),
            child: Text(
              severityLabel,
              style: TextStyle(color: severityColor, fontSize: 20, fontWeight: FontWeight.w800),
            ),
          ),
          const SizedBox(height: 20),

          // EFS Score
          Container(
            padding: const EdgeInsets.all(20),
            decoration: BoxDecoration(
              color: AppTheme.surfaceCard,
              borderRadius: BorderRadius.circular(16),
              border: Border.all(color: AppTheme.surfaceBorder),
            ),
            child: Row(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                const Text('EFS Score: ', style: TextStyle(color: AppTheme.textSecondary, fontSize: 16)),
                Text(
                  efs.toStringAsFixed(2),
                  style: TextStyle(
                    color: efs >= 0.8 ? AppTheme.success : efs >= 0.6 ? AppTheme.warning : AppTheme.danger,
                    fontSize: 24,
                    fontWeight: FontWeight.w800,
                  ),
                ),
              ],
            ),
          ),
          const SizedBox(height: 20),

          // Lesion types
          if (result['lesion_masks_rle'] != null)
            Container(
              width: double.infinity,
              padding: const EdgeInsets.all(16),
              decoration: BoxDecoration(
                color: AppTheme.surfaceCard,
                borderRadius: BorderRadius.circular(16),
                border: Border.all(color: AppTheme.surfaceBorder),
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Text('Detected Lesions', style: TextStyle(fontWeight: FontWeight.w700, fontSize: 14)),
                  const SizedBox(height: 12),
                  Wrap(
                    spacing: 8,
                    runSpacing: 8,
                    children: (result['lesion_masks_rle'] as Map).keys.map((lesion) {
                      final color = AppTheme.lesionColors[lesion] ?? AppTheme.textMuted;
                      return Chip(
                        label: Text(AppConstants.lesionLabels[lesion] ?? lesion, style: TextStyle(color: color, fontSize: 12, fontWeight: FontWeight.w600)),
                        backgroundColor: color.withOpacity(0.1),
                        side: BorderSide(color: color.withOpacity(0.3)),
                      );
                    }).toList(),
                  ),
                ],
              ),
            ),
          const SizedBox(height: 28),

          // Action buttons
          if (severity >= 2)
            SizedBox(
              width: double.infinity,
              child: ElevatedButton.icon(
                onPressed: () {
                  ScaffoldMessenger.of(context).showSnackBar(
                    const SnackBar(content: Text('Referral queued offline ✓'), backgroundColor: AppTheme.success),
                  );
                  Navigator.of(context).pop();
                },
                icon: const Icon(Icons.send),
                label: const Text('Refer Patient'),
                style: ElevatedButton.styleFrom(
                  backgroundColor: AppTheme.danger,
                  padding: const EdgeInsets.symmetric(vertical: 16),
                ),
              ),
            ),
          const SizedBox(height: 12),
          SizedBox(
            width: double.infinity,
            child: OutlinedButton.icon(
              onPressed: () {
                context.read<CaptureBloc>().add(CaptureReset());
                _startCapture();
                _simulateQualityGate();
              },
              icon: const Icon(Icons.refresh),
              label: const Text('Capture Other Eye'),
            ),
          ),
        ],
      ),
    );
  }

  @override
  void dispose() {
    _pulseController.dispose();
    super.dispose();
  }
}
