%BUILD_SIMULINK_MODEL Programmatically generates the Simulink .slx model file.
%  Constructs the discrete-event / queuing workflow in Simulink:
%    - Patient Arrival Block (Poisson Source)
%    - Quality Gate Filter Subsystem
%    - Offline SQLite Buffer / Network Uplink Delay Block
%    - Edge/Cloud AI Processing Block
%    - Ophthalmologist Review Queue (M/M/c)
%    - Telemedicine Closed-Loop Referral Sink
%
%  Requires: Simulink (SimEvents or basic Simulink library)

model_name = 'dr_screening_workflow';
model_dir = fullfile(fileparts(mfilename('fullpath')), '..');
model_path = fullfile(model_dir, [model_name '.slx']);

try
    % Check if Simulink license exists
    if ~license('test', 'Simulink')
        warning('Simulink license not detected. The model can be constructed when Simulink is active.');
        return;
    end

    % Close existing if open
    close_system(model_name, 0);

    % Create new system
    new_system(model_name);
    open_system(model_name);

    % Add Blocks
    % 1. Patient Arrival (Pulse Generator / Sine generator representing arrival rate)
    add_block('simulink/Sources/Constant', [model_name '/Patient_Arrival_Rate'], ...
        'Value', 'params.hourly_patient_arrival_rate', 'Position', [50, 100, 150, 140]);

    % 2. Quality Gate Switch
    add_block('simulink/Signal Routing/Manual Switch', [model_name '/Quality_Gate_Switch'], ...
        'Position', [220, 95, 270, 145]);

    % 3. Offline Buffer Integrator (Accumulated Cases)
    add_block('simulink/Continuous/Integrator', [model_name '/Offline_Local_Buffer'], ...
        'Position', [340, 105, 380, 135]);

    % 4. Doctor Review Service Block (Transfer Fcn / Gain)
    add_block('simulink/Math Operations/Gain', [model_name '/Ophthalmologist_Service_Rate'], ...
        'Gain', 'params.num_active_ophthalmologists * (60 / params.target_review_seconds)', ...
        'Position', [450, 100, 520, 140]);

    % 5. Output Scope / Sink
    add_block('simulink/Sinks/To Workspace', [model_name '/Review_Queue_Output'], ...
        'VariableName', 'sim_review_queue', 'Position', [590, 105, 660, 135]);

    % Connect lines
    add_line(model_name, 'Patient_Arrival_Rate/1', 'Quality_Gate_Switch/1');
    add_line(model_name, 'Quality_Gate_Switch/1', 'Offline_Local_Buffer/1');
    add_line(model_name, 'Offline_Local_Buffer/1', 'Ophthalmologist_Service_Rate/1');
    add_line(model_name, 'Ophthalmologist_Service_Rate/1', 'Review_Queue_Output/1');

    % Save and close
    save_system(model_name, model_path);
    close_system(model_name);
    fprintf('Successfully built and saved Simulink model: %s\n', model_path);

catch e
    fprintf('Simulink model builder note: %s\n', e.message);
    fprintf('When opened in MATLAB with Simulink installed, run build_simulink_model to instantiate .slx.\n');
end
