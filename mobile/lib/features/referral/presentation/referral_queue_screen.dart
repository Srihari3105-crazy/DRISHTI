import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import '../../../core/theme.dart';
import '../../../core/constants.dart';
import 'sync_bloc.dart';

class ReferralQueueScreen extends StatefulWidget {
  const ReferralQueueScreen({super.key});
  @override
  State<ReferralQueueScreen> createState() => _ReferralQueueScreenState();
}

class _ReferralQueueScreenState extends State<ReferralQueueScreen> {
  @override
  void initState() {
    super.initState();
    context.read<SyncBloc>().add(QueueLoadRequested());
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Referral Queue'),
        actions: [
          IconButton(
            icon: const Icon(Icons.sync),
            onPressed: () {
              context.read<SyncBloc>().add(SyncRequested());
            },
          ),
        ],
      ),
      body: BlocBuilder<SyncBloc, SyncState>(
        builder: (context, state) {
          if (state is SyncInProgress) {
            return const Center(child: CircularProgressIndicator());
          }
          if (state is SyncError) {
            return Center(
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  const Icon(Icons.cloud_off, size: 48, color: AppTheme.textMuted),
                  const SizedBox(height: 16),
                  Text('Offline — queue saved locally', style: TextStyle(color: AppTheme.textMuted)),
                  const SizedBox(height: 8),
                  Text(state.message, style: TextStyle(color: AppTheme.danger, fontSize: 12)),
                ],
              ),
            );
          }
          if (state is QueueLoaded) {
            if (state.referrals.isEmpty) {
              return const Center(
                child: Column(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    Icon(Icons.inbox, size: 64, color: AppTheme.textMuted),
                    SizedBox(height: 16),
                    Text('No referrals in queue', style: TextStyle(color: AppTheme.textMuted, fontSize: 16)),
                  ],
                ),
              );
            }
            return ListView.builder(
              padding: const EdgeInsets.all(16),
              itemCount: state.referrals.length,
              itemBuilder: (context, index) {
                final ref = state.referrals[index];
                final severity = ref['severity_level'] as int? ?? 0;
                final severityColor = AppTheme.severityColors[severity] ?? AppTheme.textMuted;

                return Card(
                  margin: const EdgeInsets.only(bottom: 10),
                  child: Padding(
                    padding: const EdgeInsets.all(16),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Row(
                          children: [
                            Text(
                              ref['referral_code'] ?? '—',
                              style: const TextStyle(fontFamily: 'monospace', fontWeight: FontWeight.w700, color: AppTheme.primary),
                            ),
                            const Spacer(),
                            Container(
                              padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                              decoration: BoxDecoration(
                                color: severityColor.withOpacity(0.15),
                                borderRadius: BorderRadius.circular(20),
                              ),
                              child: Text(
                                AppConstants.severityLabels[severity] ?? 'Unknown',
                                style: TextStyle(color: severityColor, fontSize: 12, fontWeight: FontWeight.w600),
                              ),
                            ),
                          ],
                        ),
                        const SizedBox(height: 8),
                        Text(
                          '${ref['patient_name'] ?? 'Patient'} · ${ref['eye'] ?? ''} · EFS ${(ref['efs_score'] as num?)?.toStringAsFixed(2) ?? '—'}',
                          style: const TextStyle(color: AppTheme.textSecondary, fontSize: 13),
                        ),
                        const SizedBox(height: 4),
                        Text(
                          'State: ${ref['state'] ?? 'queued'}',
                          style: const TextStyle(color: AppTheme.textMuted, fontSize: 12),
                        ),
                      ],
                    ),
                  ),
                );
              },
            );
          }
          return const SizedBox.shrink();
        },
      ),
    );
  }
}
