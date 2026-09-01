import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';

/// DRISHTI-LENS Theme — Dark, high-contrast for outdoor/sunlight use
class AppTheme {
  // Colors
  static const Color primary = Color(0xFF3B82F6);
  static const Color primaryDark = Color(0xFF1D4ED8);
  static const Color accent = Color(0xFF14B8A6);
  static const Color surfaceBg = Color(0xFF0A0F1A);
  static const Color surfaceCard = Color(0xFF111827);
  static const Color surfaceElevated = Color(0xFF1F2937);
  static const Color surfaceBorder = Color(0xFF374151);
  static const Color textPrimary = Color(0xFFF8FAFC);
  static const Color textSecondary = Color(0xFF94A3B8);
  static const Color textMuted = Color(0xFF64748B);
  static const Color success = Color(0xFF22C55E);
  static const Color warning = Color(0xFFF59E0B);
  static const Color danger = Color(0xFFEF4444);

  // Severity colors
  static const Map<int, Color> severityColors = {
    0: Color(0xFF22C55E),
    1: Color(0xFFEAB308),
    2: Color(0xFFF97316),
    3: Color(0xFFEF4444),
    4: Color(0xFFDC2626),
  };

  // Lesion colors for overlay
  static const Map<String, Color> lesionColors = {
    'MA': Color(0xFFEF4444),
    'HE': Color(0xFFF97316),
    'EX': Color(0xFFEAB308),
    'CWS': Color(0xFF8B5CF6),
    'VB': Color(0xFFEC4899),
    'IRMA': Color(0xFF14B8A6),
    'NV': Color(0xFFDC2626),
  };

  static ThemeData get darkTheme {
    return ThemeData(
      useMaterial3: true,
      brightness: Brightness.dark,
      scaffoldBackgroundColor: surfaceBg,
      colorScheme: const ColorScheme.dark(
        primary: primary,
        secondary: accent,
        surface: surfaceCard,
        error: danger,
        onPrimary: Colors.white,
        onSecondary: Colors.white,
        onSurface: textPrimary,
      ),
      textTheme: GoogleFonts.interTextTheme(ThemeData.dark().textTheme).copyWith(
        headlineLarge: const TextStyle(fontWeight: FontWeight.w800, color: textPrimary),
        headlineMedium: const TextStyle(fontWeight: FontWeight.w700, color: textPrimary),
        titleLarge: const TextStyle(fontWeight: FontWeight.w700, color: textPrimary),
        titleMedium: const TextStyle(fontWeight: FontWeight.w600, color: textPrimary),
        bodyLarge: const TextStyle(color: textSecondary),
        bodyMedium: const TextStyle(color: textSecondary),
        labelLarge: const TextStyle(fontWeight: FontWeight.w600, color: textPrimary),
      ),
      appBarTheme: const AppBarTheme(
        backgroundColor: surfaceBg,
        foregroundColor: textPrimary,
        elevation: 0,
        centerTitle: true,
      ),
      cardTheme: CardThemeData(
        color: surfaceCard,
        elevation: 0,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(16),
          side: const BorderSide(color: surfaceBorder, width: 1),
        ),
      ),
      elevatedButtonTheme: ElevatedButtonThemeData(
        style: ElevatedButton.styleFrom(
          backgroundColor: primary,
          foregroundColor: Colors.white,
          padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 14),
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
          textStyle: const TextStyle(fontWeight: FontWeight.w600, fontSize: 15),
        ),
      ),
      outlinedButtonTheme: OutlinedButtonThemeData(
        style: OutlinedButton.styleFrom(
          foregroundColor: textSecondary,
          side: const BorderSide(color: surfaceBorder),
          padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 14),
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
        ),
      ),
      inputDecorationTheme: InputDecorationTheme(
        filled: true,
        fillColor: surfaceElevated,
        border: OutlineInputBorder(
          borderRadius: BorderRadius.circular(12),
          borderSide: const BorderSide(color: surfaceBorder),
        ),
        enabledBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(12),
          borderSide: const BorderSide(color: surfaceBorder),
        ),
        focusedBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(12),
          borderSide: const BorderSide(color: primary, width: 2),
        ),
        labelStyle: const TextStyle(color: textMuted),
        hintStyle: const TextStyle(color: textMuted),
        contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
      ),
      bottomNavigationBarTheme: const BottomNavigationBarThemeData(
        backgroundColor: surfaceCard,
        selectedItemColor: primary,
        unselectedItemColor: textMuted,
      ),
      dividerTheme: const DividerThemeData(color: surfaceBorder, thickness: 1),
      snackBarTheme: SnackBarThemeData(
        backgroundColor: surfaceElevated,
        contentTextStyle: const TextStyle(color: textPrimary),
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
        behavior: SnackBarBehavior.floating,
      ),
    );
  }
}
