import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:equatable/equatable.dart';
import '../data/patient_repository.dart';

// Events
abstract class PatientEvent extends Equatable {
  @override
  List<Object?> get props => [];
}

class PatientsLoadRequested extends PatientEvent {
  final String? search;
  PatientsLoadRequested({this.search});
}

class PatientCreateRequested extends PatientEvent {
  final Map<String, dynamic> data;
  PatientCreateRequested(this.data);
}

// States
abstract class PatientState extends Equatable {
  @override
  List<Object?> get props => [];
}

class PatientInitial extends PatientState {}
class PatientLoading extends PatientState {}

class PatientsLoaded extends PatientState {
  final List<Map<String, dynamic>> patients;
  PatientsLoaded(this.patients);
  @override
  List<Object?> get props => [patients];
}

class PatientCreated extends PatientState {
  final Map<String, dynamic> patient;
  PatientCreated(this.patient);
}

class PatientError extends PatientState {
  final String message;
  PatientError(this.message);
  @override
  List<Object?> get props => [message];
}

class PatientBloc extends Bloc<PatientEvent, PatientState> {
  final PatientRepository _repo;

  PatientBloc(this._repo) : super(PatientInitial()) {
    on<PatientsLoadRequested>(_onLoad);
    on<PatientCreateRequested>(_onCreate);
  }

  Future<void> _onLoad(PatientsLoadRequested event, Emitter<PatientState> emit) async {
    emit(PatientLoading());
    try {
      final patients = await _repo.getPatients(search: event.search);
      emit(PatientsLoaded(patients));
    } catch (e) {
      emit(PatientError(e.toString()));
    }
  }

  Future<void> _onCreate(PatientCreateRequested event, Emitter<PatientState> emit) async {
    emit(PatientLoading());
    try {
      final patient = await _repo.createPatient(event.data);
      emit(PatientCreated(patient));
    } catch (e) {
      emit(PatientError(e.toString()));
    }
  }
}
