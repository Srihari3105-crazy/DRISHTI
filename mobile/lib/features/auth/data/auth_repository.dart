import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:dio/dio.dart';
import '../../../core/constants.dart';

class AuthRepository {
  final _storage = const FlutterSecureStorage();
  final _dio = Dio(BaseOptions(baseUrl: AppConstants.apiBaseUrl));

  Future<Map<String, dynamic>> login(String phone, String password) async {
    final response = await _dio.post('/auth/login', data: {
      'phone': phone,
      'password': password,
    });

    final data = response.data;
    await _storage.write(key: 'access_token', value: data['access_token']);
    await _storage.write(key: 'refresh_token', value: data['refresh_token']);
    await _storage.write(key: 'user_id', value: data['user']['id']);
    await _storage.write(key: 'user_name', value: data['user']['name']);
    await _storage.write(key: 'user_role', value: data['user']['role']);

    return data['user'];
  }

  Future<String?> getToken() async => await _storage.read(key: 'access_token');
  Future<String?> getUserName() async => await _storage.read(key: 'user_name');
  Future<String?> getUserRole() async => await _storage.read(key: 'user_role');
  Future<String?> getUserId() async => await _storage.read(key: 'user_id');

  Future<bool> isLoggedIn() async {
    final token = await getToken();
    return token != null && token.isNotEmpty;
  }

  Future<void> logout() async {
    await _storage.deleteAll();
  }

  Dio getAuthenticatedDio() {
    final dio = Dio(BaseOptions(baseUrl: AppConstants.apiBaseUrl));
    dio.interceptors.add(InterceptorsWrapper(
      onRequest: (options, handler) async {
        final token = await getToken();
        if (token != null) {
          options.headers['Authorization'] = 'Bearer $token';
        }
        handler.next(options);
      },
    ));
    return dio;
  }
}
