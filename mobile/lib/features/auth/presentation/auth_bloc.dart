import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:equatable/equatable.dart';
import '../data/auth_repository.dart';

// Events
abstract class AuthEvent extends Equatable {
  @override
  List<Object?> get props => [];
}

class AuthLoginRequested extends AuthEvent {
  final String phone;
  final String password;
  AuthLoginRequested(this.phone, this.password);
  @override
  List<Object?> get props => [phone, password];
}

class AuthLogoutRequested extends AuthEvent {}

class AuthCheckRequested extends AuthEvent {}

// States
abstract class AuthState extends Equatable {
  @override
  List<Object?> get props => [];
}

class AuthInitial extends AuthState {}
class AuthLoading extends AuthState {}

class AuthAuthenticated extends AuthState {
  final String userId;
  final String userName;
  final String userRole;
  AuthAuthenticated({required this.userId, required this.userName, required this.userRole});
  @override
  List<Object?> get props => [userId, userName, userRole];
}

class AuthUnauthenticated extends AuthState {}

class AuthError extends AuthState {
  final String message;
  AuthError(this.message);
  @override
  List<Object?> get props => [message];
}

// Bloc
class AuthBloc extends Bloc<AuthEvent, AuthState> {
  final AuthRepository _repo;

  AuthBloc(this._repo) : super(AuthInitial()) {
    on<AuthLoginRequested>(_onLogin);
    on<AuthLogoutRequested>(_onLogout);
    on<AuthCheckRequested>(_onCheck);
  }

  Future<void> _onLogin(AuthLoginRequested event, Emitter<AuthState> emit) async {
    emit(AuthLoading());
    try {
      final user = await _repo.login(event.phone, event.password);
      emit(AuthAuthenticated(
        userId: user['id'],
        userName: user['name'],
        userRole: user['role'],
      ));
    } catch (e) {
      String message = 'Login failed';
      if (e is Exception) {
        message = e.toString().replaceFirst('Exception: ', '');
      }
      emit(AuthError(message));
    }
  }

  Future<void> _onLogout(AuthLogoutRequested event, Emitter<AuthState> emit) async {
    await _repo.logout();
    emit(AuthUnauthenticated());
  }

  Future<void> _onCheck(AuthCheckRequested event, Emitter<AuthState> emit) async {
    final isLoggedIn = await _repo.isLoggedIn();
    if (isLoggedIn) {
      final name = await _repo.getUserName() ?? '';
      final role = await _repo.getUserRole() ?? '';
      final id = await _repo.getUserId() ?? '';
      emit(AuthAuthenticated(userId: id, userName: name, userRole: role));
    } else {
      emit(AuthUnauthenticated());
    }
  }
}
