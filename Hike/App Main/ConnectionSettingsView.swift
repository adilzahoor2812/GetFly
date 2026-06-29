//
//  ConnectionSettingsView.swift
//  Hike
//

import SwiftUI

struct ConnectionSettingsView: View {
    @ObservedObject var settings: DroneConnectionSettings
    @ObservedObject var viewModel: DroneViewModel
    @Environment(\.dismiss) private var dismiss

    var body: some View {
        NavigationStack {
            Form {
                Section("ESP32 Network") {
                    TextField("IP Address", text: $settings.hostAddress)
                        .keyboardType(.decimalPad)
                        .textInputAutocapitalization(.never)
                        .autocorrectionDisabled()

                    Stepper("Port: \(settings.port)", value: $settings.port, in: 1...65535)

                    Slider(value: $settings.pollIntervalSeconds, in: 0.5...3, step: 0.5) {
                        Text("Status Poll Interval")
                    } minimumValueLabel: {
                        Text("0.5s")
                    } maximumValueLabel: {
                        Text("3s")
                    }

                    Text("Poll every \(String(format: "%.1f", settings.pollIntervalSeconds)) seconds")
                        .font(.caption)
                        .foregroundStyle(.secondary)
                }

                Section("Default ESP32 AP") {
                    Text("When the ESP32 runs as a Wi‑Fi access point, the default address is usually 192.168.4.1 on port 80.")
                        .font(.caption)
                        .foregroundStyle(.secondary)
                }

                Section {
                    Button("Test Connection") {
                        Task { await viewModel.refreshStatus() }
                    }
                }
            }
            .navigationTitle("Connection")
            .toolbar {
                ToolbarItem(placement: .confirmationAction) {
                    Button("Done") { dismiss() }
                }
            }
        }
    }
}

#Preview {
    ConnectionSettingsView(settings: DroneConnectionSettings(), viewModel: DroneViewModel())
}
