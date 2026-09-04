import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:go_router/go_router.dart';
import '../../../core/theme.dart';
import 'patient_bloc.dart';

class PatientListScreen extends StatefulWidget {
  const PatientListScreen({super.key});
  @override
  State<PatientListScreen> createState() => _PatientListScreenState();
}

class _PatientListScreenState extends State<PatientListScreen> {
  final _searchController = TextEditingController();

  @override
  void initState() {
    super.initState();
    context.read<PatientBloc>().add(PatientsLoadRequested());
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Patients'),
        actions: [
          IconButton(
            icon: const Icon(Icons.person_add),
            onPressed: () => context.push('/patients/register'),
          ),
        ],
      ),
      body: Column(
        children: [
          // Search bar
          Padding(
            padding: const EdgeInsets.all(16),
            child: TextField(
              controller: _searchController,
              decoration: InputDecoration(
                hintText: 'Search by name or mobile...',
                prefixIcon: const Icon(Icons.search, color: AppTheme.textMuted),
                suffixIcon: _searchController.text.isNotEmpty
                    ? IconButton(
                        icon: const Icon(Icons.clear, size: 18),
                        onPressed: () {
                          _searchController.clear();
                          context.read<PatientBloc>().add(PatientsLoadRequested());
                        },
                      )
                    : null,
              ),
              onChanged: (value) {
                context.read<PatientBloc>().add(PatientsLoadRequested(search: value));
              },
            ),
          ),

          // Patient list
          Expanded(
            child: BlocBuilder<PatientBloc, PatientState>(
              builder: (context, state) {
                if (state is PatientLoading) {
                  return const Center(child: CircularProgressIndicator());
                }
                if (state is PatientError) {
                  return Center(child: Text(state.message, style: TextStyle(color: AppTheme.danger)));
                }
                if (state is PatientsLoaded) {
                  if (state.patients.isEmpty) {
                    return const Center(
                      child: Column(
                        mainAxisAlignment: MainAxisAlignment.center,
                        children: [
                          Icon(Icons.people_outline, size: 64, color: AppTheme.textMuted),
                          SizedBox(height: 16),
                          Text('No patients found', style: TextStyle(color: AppTheme.textMuted)),
                        ],
                      ),
                    );
                  }
                  return ListView.builder(
                    padding: const EdgeInsets.symmetric(horizontal: 16),
                    itemCount: state.patients.length,
                    itemBuilder: (context, index) {
                      final p = state.patients[index];
                      return Card(
                        margin: const EdgeInsets.only(bottom: 10),
                        child: ListTile(
                          contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
                          leading: CircleAvatar(
                            backgroundColor: AppTheme.primary.withValues(alpha: 0.15),
                            child: Text(
                              ((p['name'] as String?)?.isNotEmpty == true ? (p['name'] as String).substring(0, 1).toUpperCase() : '?'),
                              style: const TextStyle(color: AppTheme.primary, fontWeight: FontWeight.w700),
                            ),
                          ),
                          title: Text(p['name'], style: const TextStyle(fontWeight: FontWeight.w600)),
                          subtitle: Text(
                            'Age ${p['age']} · ${p['mobile']}',
                            style: const TextStyle(color: AppTheme.textMuted, fontSize: 13),
                          ),
                          trailing: Row(
                            mainAxisSize: MainAxisSize.min,
                            children: [
                              if (p['mobile_verified'] == true)
                                Container(
                                  padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                                  decoration: BoxDecoration(
                                    color: AppTheme.success.withValues(alpha: 0.15),
                                    borderRadius: BorderRadius.circular(20),
                                  ),
                                  child: const Text('✓', style: TextStyle(color: AppTheme.success, fontSize: 12)),
                                ),
                              const SizedBox(width: 8),
                              ElevatedButton.icon(
                                onPressed: () => context.push('/capture/${p['id']}'),
                                icon: const Icon(Icons.camera_alt, size: 16),
                                label: const Text('Capture', style: TextStyle(fontSize: 13)),
                                style: ElevatedButton.styleFrom(
                                  padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
                                ),
                              ),
                            ],
                          ),
                        ),
                      );
                    },
                  );
                }
                return const SizedBox.shrink();
              },
            ),
          ),
        ],
      ),
    );
  }

  @override
  void dispose() {
    _searchController.dispose();
    super.dispose();
  }
}
