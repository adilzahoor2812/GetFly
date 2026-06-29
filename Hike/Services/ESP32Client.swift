//
//  ESP32Client.swift
//  Hike
//

import Foundation

enum ESP32ClientError: LocalizedError {
    case invalidURL
    case invalidResponse
    case serverError(String)

    var errorDescription: String? {
        switch self {
        case .invalidURL:
            return "Invalid ESP32 address. Check Settings."
        case .invalidResponse:
            return "Unexpected response from ESP32."
        case .serverError(let message):
            return message
        }
    }
}

actor ESP32Client {
    private let session: URLSession
    private let encoder = JSONEncoder()
    private let decoder = JSONDecoder()

    init(session: URLSession = .shared) {
        self.session = session
    }

    func fetchStatus(baseURL: URL) async throws -> DroneStatus {
        let url = baseURL.appendingPathComponent("status")
        var request = URLRequest(url: url)
        request.httpMethod = "GET"
        request.timeoutInterval = 3

        let (data, response) = try await session.data(for: request)
        try validateHTTP(response: response, data: data)
        return try decoder.decode(DroneStatus.self, from: data)
    }

    func sendCommand(_ payload: DroneCommandPayload, baseURL: URL) async throws -> DroneCommandResponse {
        let url = baseURL.appendingPathComponent("command")
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        request.httpBody = try encoder.encode(payload)
        request.timeoutInterval = 5

        let (data, response) = try await session.data(for: request)
        try validateHTTP(response: response, data: data)

        if let commandResponse = try? decoder.decode(DroneCommandResponse.self, from: data) {
            guard commandResponse.success else {
                throw ESP32ClientError.serverError(commandResponse.message ?? "Command rejected by ESP32.")
            }
            return commandResponse
        }

        return DroneCommandResponse(success: true, message: nil)
    }

    private func validateHTTP(response: URLResponse, data: Data) throws {
        guard let http = response as? HTTPURLResponse else {
            throw ESP32ClientError.invalidResponse
        }

        guard (200...299).contains(http.statusCode) else {
            let body = String(data: data, encoding: .utf8) ?? "HTTP \(http.statusCode)"
            throw ESP32ClientError.serverError(body)
        }
    }
}
