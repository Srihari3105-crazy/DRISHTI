import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:google_fonts/google_fonts.dart';

import 'core/constants.dart';
import 'core/router.dart';
import 'core/theme.dart';
import 'features/auth/data/auth_repository.dart';
import 'features/auth/presentation/auth_bloc.dart';
import 'features/patient/data/patient_repository.dart';
import 'features/patient/presentation/patient_bloc.dart';
import 'features/capture/presentation/capture_bloc.dart';
import 'features/referral/data/referral_repository.dart';
import 'features/referral/presentation/sync_bloc.dart';

void main() async {
  WidgetsFlutterBinding.ensureInitialized();

  // Lock orientation for fundus capture
  await SystemChrome.setPreferredOrientations([
    DeviceOrientation.portraitUp,
  ]);

  // Set system UI overlay style
  SystemChrome.setSystemUIOverlayStyle(const SystemUIOverlayStyle(
    statusBarColor: Colors.transparent,
    statusBarIconBrightness: Brightness.light,
    systemNavigationBarColor: Color(0xFF0A0F1A),
  ));

  runApp(const DrishtiLensApp());
}

class DrishtiLensApp extends StatelessWidget {
  const DrishtiLensApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MultiBlocProvider(
      providers: [
        BlocProvider(create: (_) => AuthBloc(AuthRepository())),
        BlocProvider(create: (_) => PatientBloc(PatientRepository())),
        BlocProvider(create: (_) => CaptureBloc()),
        BlocProvider(create: (_) => SyncBloc(ReferralRepository())),
      ],
      child: MaterialApp.router(
        title: AppConstants.appName,
        debugShowCheckedModeBanner: false,
        theme: AppTheme.darkTheme,
        routerConfig: appRouter,
      ),
    );
  }
}
