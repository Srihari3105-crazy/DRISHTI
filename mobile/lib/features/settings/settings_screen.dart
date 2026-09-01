import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import '../../core/theme.dart';
import '../../core/constants.dart';
import '../auth/presentation/auth_bloc.dart';

class SettingsScreen extends StatelessWidget {
  const SettingsScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Settings')),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          // Sync Status
          Card(
            child: Padding(
              padding: const EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Text('Sync Status', style: TextStyle(fontWeight: FontWeight.w700, fontSize: 16)),
                  const SizedBox(height: 12),
                  _statusRow('Last Sync', 'Just now', AppTheme.success),
                  _statusRow('Pending Items', '0', AppTheme.textSecondary),
                  _statusRow('Connection', 'Online', AppTheme.success),
                  const SizedBox(height: 12),
                  SizedBox(
                    width: double.infinity,
                    child: ElevatedButton.icon(
                      onPressed: () {
                        ScaffoldMessenger.of(context).showSnackBar(
                          const SnackBar(content: Text('Sync complete ✓'), backgroundColor: AppTheme.success),
                        );
                      },
                      icon: const Icon(Icons.sync, size: 18),
                      label: const Text('Sync Now'),
                    ),
                  ),
                ],
              ),
            ),
          ),
          const SizedBox(height: 12),

          // Model Info
          Card(
            child: Padding(
              padding: const EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Text('AI Models', style: TextStyle(fontWeight: FontWeight.w700, fontSize: 16)),
                  const SizedBox(height: 12),
                  _statusRow('Quality Gate', 'v1 (TFLite, 4.8MB)', AppTheme.textSecondary),
                  _statusRow('Grading Model', 'v1 (ONNX, 18.2MB)', AppTheme.textSecondary),
                  _statusRow('Mode', 'Mock (demo)', AppTheme.warning),
                ],
              ),
            ),
          ),
          const SizedBox(height: 12),

          // App Info
          Card(
            child: Padding(
              padding: const EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Text('App Info', style: TextStyle(fontWeight: FontWeight.w700, fontSize: 16)),
                  const SizedBox(height: 12),
                  _statusRow('Version', AppConstants.appVersion, AppTheme.textSecondary),
                  _statusRow('API', AppConstants.apiBaseUrl, AppTheme.textMuted),
                ],
              ),
            ),
          ),
          const SizedBox(height: 24),

          // Demo Mode Toggle
          Card(
            color: AppTheme.primary.withOpacity(0.08),
            child: ListTile(
              leading: const Icon(Icons.science, color: AppTheme.primary),
              title: const Text('Demo Mode', style: TextStyle(fontWeight: FontWeight.w600)),
              subtitle: const Text('Use pre-loaded demo images', style: TextStyle(fontSize: 12, color: AppTheme.textMuted)),
              trailing: Switch(
                value: true,
                onChanged: (v) {},
                activeColor: AppTheme.primary,
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _statusRow(String label, String value, Color valueColor) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 4),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Text(label, style: const TextStyle(color: AppTheme.textMuted, fontSize: 13)),
          Text(value, style: TextStyle(color: valueColor, fontSize: 13, fontWeight: FontWeight.w500)),
        ],
      ),
    );
  }
}
