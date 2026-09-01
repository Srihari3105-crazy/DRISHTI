import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:equatable/equatable.dart';
import '../data/referral_repository.dart';

// Events
abstract class SyncEvent extends Equatable {
  @override
  List<Object?> get props => [];
}

class SyncRequested extends SyncEvent {}
class QueueLoadRequested extends SyncEvent {}

// States
abstract class SyncState extends Equatable {
  @override
  List<Object?> get props => [];
}

class SyncInitial extends SyncState {}
class SyncInProgress extends SyncState {}

class SyncComplete extends SyncState {
  final int syncedCount;
  SyncComplete(this.syncedCount);
  @override
  List<Object?> get props => [syncedCount];
}

class QueueLoaded extends SyncState {
  final List<Map<String, dynamic>> referrals;
  QueueLoaded(this.referrals);
  @override
  List<Object?> get props => [referrals];
}

class SyncError extends SyncState {
  final String message;
  SyncError(this.message);
  @override
  List<Object?> get props => [message];
}

class SyncBloc extends Bloc<SyncEvent, SyncState> {
  final ReferralRepository _repo;

  SyncBloc(this._repo) : super(SyncInitial()) {
    on<SyncRequested>(_onSync);
    on<QueueLoadRequested>(_onLoadQueue);
  }

  Future<void> _onSync(SyncRequested event, Emitter<SyncState> emit) async {
    emit(SyncInProgress());
    try {
      final count = await _repo.syncQueue();
      emit(SyncComplete(count));
    } catch (e) {
      emit(SyncError(e.toString()));
    }
  }

  Future<void> _onLoadQueue(QueueLoadRequested event, Emitter<SyncState> emit) async {
    try {
      final referrals = await _repo.getLocalQueue();
      emit(QueueLoaded(referrals));
    } catch (e) {
      emit(SyncError(e.toString()));
    }
  }
}
