import 'package:flutter/material.dart';
import '../../../core/theme.dart';
import '../../../core/constants.dart';

class ResultScreen extends StatelessWidget {
  final String screeningId;
  const ResultScreen({super.key, required this.screeningId});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Screening Result')),
      body: Center(
        child: Padding(
          padding: const EdgeInsets.all(24),
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              const Icon(Icons.check_circle, size: 80, color: AppTheme.success),
              const SizedBox(height: 20),
              Text(
                'Screening Complete',
                style: Theme.of(context).textTheme.headlineMedium,
              ),
              const SizedBox(height: 8),
              Text(
                'ID: $screeningId',
                style: const TextStyle(color: AppTheme.textMuted, fontFamily: 'monospace'),
              ),
              const SizedBox(height: 32),
              const Text(
                'Result synced to local queue.\nWill upload when online.',
                textAlign: TextAlign.center,
                style: TextStyle(color: AppTheme.textSecondary),
              ),
              const SizedBox(height: 32),
              SizedBox(
                width: double.infinity,
                child: ElevatedButton(
                  onPressed: () => Navigator.of(context).popUntil((route) => route.isFirst),
                  child: const Text('Back to Home'),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
