import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:go_router/go_router.dart';
import '../../../core/theme.dart';
import 'patient_bloc.dart';

class RegisterPatientScreen extends StatefulWidget {
  const RegisterPatientScreen({super.key});
  @override
  State<RegisterPatientScreen> createState() => _RegisterPatientScreenState();
}

class _RegisterPatientScreenState extends State<RegisterPatientScreen> {
  final _formKey = GlobalKey<FormState>();
  final _name = TextEditingController();
  final _age = TextEditingController();
  final _mobile = TextEditingController(text: '+91');
  String _gender = 'M';
  String _districtId = 'DIST01';
  String _blockId = 'BLK01';
  String? _diabetesType;

  @override
  Widget build(BuildContext context) {
    return BlocListener<PatientBloc, PatientState>(
      listener: (context, state) {
        if (state is PatientCreated) {
          ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(content: Text('Patient registered successfully!'), backgroundColor: AppTheme.success),
          );
          context.pop();
        } else if (state is PatientError) {
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(content: Text(state.message), backgroundColor: AppTheme.danger),
          );
        }
      },
      child: Scaffold(
        appBar: AppBar(title: const Text('Register Patient')),
        body: SingleChildScrollView(
          padding: const EdgeInsets.all(20),
          child: Form(
            key: _formKey,
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                _buildField('Full Name', _name, Icons.person, validator: (v) => v!.isEmpty ? 'Required' : null),
                const SizedBox(height: 16),
                Row(
                  children: [
                    Expanded(child: _buildField('Age', _age, Icons.cake, keyboardType: TextInputType.number, validator: (v) => v!.isEmpty ? 'Required' : null)),
                    const SizedBox(width: 16),
                    Expanded(
                      child: DropdownButtonFormField<String>(
                        initialValue: _gender,
                        decoration: const InputDecoration(labelText: 'Gender', prefixIcon: Icon(Icons.wc, color: AppTheme.textMuted)),
                        items: const [
                          DropdownMenuItem(value: 'M', child: Text('Male')),
                          DropdownMenuItem(value: 'F', child: Text('Female')),
                          DropdownMenuItem(value: 'O', child: Text('Other')),
                        ],
                        onChanged: (v) => setState(() => _gender = v!),
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 16),
                _buildField('Mobile', _mobile, Icons.phone, keyboardType: TextInputType.phone, validator: (v) => v!.length < 13 ? 'Enter valid +91 number' : null),
                const SizedBox(height: 16),
                DropdownButtonFormField<String>(
                  initialValue: _diabetesType,
                  decoration: const InputDecoration(labelText: 'Diabetes Type', prefixIcon: Icon(Icons.medical_information, color: AppTheme.textMuted)),
                  items: const [
                    DropdownMenuItem(value: null, child: Text('Unknown')),
                    DropdownMenuItem(value: 'Type1', child: Text('Type 1')),
                    DropdownMenuItem(value: 'Type2', child: Text('Type 2')),
                  ],
                  onChanged: (v) => setState(() => _diabetesType = v),
                ),
                const SizedBox(height: 32),
                BlocBuilder<PatientBloc, PatientState>(
                  builder: (context, state) {
                    return ElevatedButton.icon(
                      onPressed: state is PatientLoading ? null : _submit,
                      icon: state is PatientLoading
                          ? const SizedBox(width: 18, height: 18, child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white))
                          : const Icon(Icons.person_add),
                      label: Text(state is PatientLoading ? 'Registering...' : 'Register Patient'),
                      style: ElevatedButton.styleFrom(padding: const EdgeInsets.symmetric(vertical: 16)),
                    );
                  },
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }

  Widget _buildField(String label, TextEditingController controller, IconData icon,
      {TextInputType? keyboardType, String? Function(String?)? validator}) {
    return TextFormField(
      controller: controller,
      keyboardType: keyboardType,
      validator: validator,
      decoration: InputDecoration(
        labelText: label,
        prefixIcon: Icon(icon, color: AppTheme.textMuted),
      ),
    );
  }

  void _submit() {
    if (!_formKey.currentState!.validate()) return;
    context.read<PatientBloc>().add(PatientCreateRequested({
      'name': _name.text.trim(),
      'age': int.parse(_age.text.trim()),
      'gender': _gender,
      'mobile': _mobile.text.trim(),
      'district_id': _districtId,
      'block_id': _blockId,
      if (_diabetesType != null) 'diabetes_type': _diabetesType,
    }));
  }

  @override
  void dispose() {
    _name.dispose();
    _age.dispose();
    _mobile.dispose();
    super.dispose();
  }
}
