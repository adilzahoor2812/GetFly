//
//  DroneViewModel.swift
//  Hike
//

import Foundation

@MainActor
final class DroneViewModel: ObservableObject {
    @Published var status: DroneStatus = .disconnected
    @Published var isConnected = false
    @Published var isBusy = false
    @Published var lastError: String?
    @Published var lastSuccessMessage: String?

    @Published var targetCoordinate = Coordinate3D(x: 0, y: 0, z: 1.5)
    @Published var waypoints: [Waypoint] = []

    let settings = DroneConnectionSettings()
    private let client = ESP32Client()
    private var pollingTask: Task<Void, Never>?

    func startPolling() {
        pollingTask?.cancel()
        pollingTask = Task {
            while !Task.isCancelled {
                await refreshStatus()
                let interval = settings.pollIntervalSeconds
                try? await Task.sleep(for: .seconds(interval))
            }
        }
    }

    func stopPolling() {
        pollingTask?.cancel()
        pollingTask = nil
    }

    func refreshStatus() async {
        guard let baseURL = settings.baseURL else {
            isConnected = false
            lastError = ESP32ClientError.invalidURL.localizedDescription
            return
        }

        do {
            let newStatus = try await client.fetchStatus(baseURL: baseURL)
            status = newStatus
            isConnected = true
            lastError = nil
        } catch {
            isConnected = false
            status = .disconnected
            lastError = error.localizedDescription
        }
    }

    func sendAction(_ action: DroneAction) async {
        await send(payload: .action(action))
    }

    func sendGoto() async {
        await send(payload: .goto(targetCoordinate))
    }

    func sendMission() async {
        guard !waypoints.isEmpty else {
            lastError = "Add at least one waypoint to the mission."
            return
        }
        await send(payload: .mission(waypoints))
    }

    func addWaypoint(from coordinate: Coordinate3D? = nil) {
        let point = coordinate ?? targetCoordinate
        waypoints.append(Waypoint(coordinate: point))
    }

    func removeWaypoint(at offsets: IndexSet) {
        waypoints.remove(atOffsets: offsets)
    }

    func moveWaypoint(from source: IndexSet, to destination: Int) {
        waypoints.move(fromOffsets: source, toOffset: destination)
    }

    private func send(payload: DroneCommandPayload) async {
        guard let baseURL = settings.baseURL else {
            lastError = ESP32ClientError.invalidURL.localizedDescription
            return
        }

        isBusy = true
        defer { isBusy = false }

        do {
            let response = try await client.sendCommand(payload, baseURL: baseURL)
            lastSuccessMessage = response.message ?? "Command sent."
            lastError = nil
            await refreshStatus()
        } catch {
            lastError = error.localizedDescription
        }
    }
}
