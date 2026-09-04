import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:go_router/go_router.dart';
import '../../core/theme.dart';
import '../../features/auth/presentation/auth_bloc.dart';

class HomeScreen extends StatelessWidget {
  const HomeScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return BlocBuilder<AuthBloc, AuthState>(
      builder: (context, state) {
        final userName = state is AuthAuthenticated ? state.userName : 'Operator';

        return Scaffold(
          body: SafeArea(
            child: Padding(
              padding: const EdgeInsets.all(20),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  // Header
                  Row(
                    children: [
                      Container(
                        padding: const EdgeInsets.all(10),
                        decoration: BoxDecoration(
                          gradient: const LinearGradient(colors: [AppTheme.primary, AppTheme.accent]),
                          borderRadius: BorderRadius.circular(14),
                        ),
                        child: const Icon(Icons.remove_red_eye_outlined, color: Colors.white, size: 24),
                      ),
                      const SizedBox(width: 12),
                      Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          const Text('DRISHTI-LENS', style: TextStyle(fontWeight: FontWeight.w800, fontSize: 18, letterSpacing: 1)),
                          Text('Welcome, $userName', style: const TextStyle(color: AppTheme.textMuted, fontSize: 13)),
                        ],
                      ),
                      const Spacer(),
                      IconButton(
                        icon: const Icon(Icons.logout, color: AppTheme.textMuted),
                        onPressed: () {
                          context.read<AuthBloc>().add(AuthLogoutRequested());
                          context.go('/login');
                        },
                      ),
                    ],
                  ),
                  const SizedBox(height: 32),

                  // Quick Actions Grid
                  Expanded(
                    child: GridView.count(
                      crossAxisCount: 2,
                      crossAxisSpacing: 14,
                      mainAxisSpacing: 14,
                      children: [
                        _actionCard(context, '📋', 'Patients', 'Register & view', '/patients', AppTheme.primary),
                        _actionCard(context, '📸', 'Capture', 'Select patient first', '/patients', AppTheme.accent),
                        _actionCard(context, '📤', 'Referral Queue', 'View & sync', '/referrals', const Color(0xFF8B5CF6)),
                        _actionCard(context, '⚙️', 'Settings', 'Sync & model info', '/settings', AppTheme.textMuted),
                      ],
                    ),
                  ),

                  // Status bar
                  Container(
                    padding: const EdgeInsets.all(14),
                    decoration: BoxDecoration(
                      color: AppTheme.surfaceCard,
                      borderRadius: BorderRadius.circular(14),
                      border: Border.all(color: AppTheme.surfaceBorder),
                    ),
                    child: Row(
                      children: [
                        Container(
                          width: 8, height: 8,
                          decoration: const BoxDecoration(shape: BoxShape.circle, color: AppTheme.success),
                        ),
                        const SizedBox(width: 10),
                        const Text('Offline-ready', style: TextStyle(color: AppTheme.textSecondary, fontSize: 13)),
                        const Spacer(),
                        const Text('v1.0.0-mvp', style: TextStyle(color: AppTheme.textMuted, fontSize: 12, fontFamily: 'monospace')),
                      ],
                    ),
                  ),
                ],
              ),
            ),
          ),
        );
      },
    );
  }

  Widget _actionCard(BuildContext context, String emoji, String title, String subtitle, String route, Color color) {
    return GestureDetector(
      onTap: () => context.push(route),
      child: Container(
        padding: const EdgeInsets.all(20),
        decoration: BoxDecoration(
          color: AppTheme.surfaceCard,
          borderRadius: BorderRadius.circular(18),
          border: Border.all(color: AppTheme.surfaceBorder),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(emoji, style: const TextStyle(fontSize: 32)),
            const Spacer(),
            Text(title, style: const TextStyle(fontWeight: FontWeight.w700, fontSize: 16)),
            const SizedBox(height: 4),
            Text(subtitle, style: const TextStyle(color: AppTheme.textMuted, fontSize: 12)),
          ],
        ),
      ),
    );
  }
}
