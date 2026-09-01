import 'package:dio/dio.dart';
import '../../auth/data/auth_repository.dart';

class ReferralRepository {
  final AuthRepository _authRepo = AuthRepository();

  Future<Map<String, dynamic>> submitScreening(Map<String, dynamic> data) async {
    final dio = _authRepo.getAuthenticatedDio();
    final response = await dio.post('/screenings', data: {
      ...data,
      'auto_refer': true,
    });
    return response.data;
  }

  Future<List<Map<String, dynamic>>> getLocalQueue() async {
    // In MVP, this returns from API (later: local SQLite)
    final dio = _authRepo.getAuthenticatedDio();
    final response = await dio.get('/referrals', queryParameters: {'page': 1, 'size': 50});
    return List<Map<String, dynamic>>.from(response.data['items'] ?? []);
  }

  Future<int> syncQueue() async {
    // In a real implementation, this would:
    // 1. Read from local SQLite sync_queue
    // 2. POST each screening to the server
    // 3. Mark synced items
    // For MVP, data goes directly to server
    return 0;
  }
}
