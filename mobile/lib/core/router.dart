import 'package:go_router/go_router.dart';
import '../features/auth/presentation/login_screen.dart';
import '../features/patient/presentation/patient_list_screen.dart';
import '../features/patient/presentation/register_patient_screen.dart';
import '../features/capture/presentation/camera_screen.dart';
import '../features/capture/presentation/result_screen.dart';
import '../features/referral/presentation/referral_queue_screen.dart';
import '../features/settings/settings_screen.dart';
import '../shared/screens/home_screen.dart';

final GoRouter appRouter = GoRouter(
  initialLocation: '/login',
  routes: [
    GoRoute(path: '/login', builder: (_, __) => const LoginScreen()),
    GoRoute(path: '/home', builder: (_, __) => const HomeScreen()),
    GoRoute(path: '/patients', builder: (_, __) => const PatientListScreen()),
    GoRoute(path: '/patients/register', builder: (_, __) => const RegisterPatientScreen()),
    GoRoute(
      path: '/capture/:patientId',
      builder: (_, state) => CameraScreen(
        patientId: state.pathParameters['patientId']!,
      ),
    ),
    GoRoute(
      path: '/result/:screeningId',
      builder: (_, state) => ResultScreen(
        screeningId: state.pathParameters['screeningId']!,
      ),
    ),
    GoRoute(path: '/referrals', builder: (_, __) => const ReferralQueueScreen()),
    GoRoute(path: '/settings', builder: (_, __) => const SettingsScreen()),
  ],
);
