import '../../auth/data/auth_repository.dart';

class PatientRepository {
  final AuthRepository _authRepo = AuthRepository();

  Future<List<Map<String, dynamic>>> getPatients({String? search}) async {
    final dio = _authRepo.getAuthenticatedDio();
    final params = <String, dynamic>{'page': 1, 'size': 50};
    if (search != null && search.isNotEmpty) params['search'] = search;

    final response = await dio.get('/patients', queryParameters: params);
    return List<Map<String, dynamic>>.from(response.data);
  }

  Future<Map<String, dynamic>> createPatient(Map<String, dynamic> data) async {
    final dio = _authRepo.getAuthenticatedDio();
    final response = await dio.post('/patients', data: data);
    return response.data;
  }

  Future<Map<String, dynamic>> sendOTP(String patientId, String mobile) async {
    final dio = _authRepo.getAuthenticatedDio();
    final response = await dio.post('/patients/$patientId/verify-mobile', data: {'mobile': mobile});
    return response.data;
  }

  Future<Map<String, dynamic>> verifyOTP(String patientId, String otp) async {
    final dio = _authRepo.getAuthenticatedDio();
    final response = await dio.post('/patients/$patientId/confirm-mobile', data: {'otp': otp});
    return response.data;
  }
}
