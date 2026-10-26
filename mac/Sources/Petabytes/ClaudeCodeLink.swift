import Foundation
import Network

/**
 Lets Claude Code drive the pet: the Petabytes add-on for Claude Code posts what Claude is doing (starting a task,
 reading, editing, running tests, finishing) to this app on 127.0.0.1, never over the network. Each request is
 one small JSON reaction, `{"type": "react", "key": "claudeDone"}`; keys that pets.json doesn't know are ignored.
 */
final class ClaudeCodeLink {
    /** Where the add-on finds the app; it's in the add-on too. */
    static let port: UInt16 = 47_365

    private var listener: NWListener?
    var onReact: ([String: Any]) -> Void = { _ in }

    func start() {
        guard listener == nil, let port = NWEndpoint.Port(rawValue: Self.port) else { return }
        let parameters = NWParameters.tcp
        parameters.requiredLocalEndpoint = .hostPort(host: .ipv4(.loopback), port: port)
        parameters.allowLocalEndpointReuse = true
        guard let listener = try? NWListener(using: parameters) else { return }
        listener.newConnectionHandler = { [weak self] connection in
            connection.start(queue: .main)
            self?.read(connection, Data())
        }
        listener.start(queue: .main)
        self.listener = listener
    }

    func stop() {
        listener?.cancel()
        listener = nil
    }

    /** Reads until the request is whole (headers, then Content-Length bytes of body), answers, and hangs up. */
    private func read(_ connection: NWConnection, _ received: Data) {
        connection.receive(minimumIncompleteLength: 1, maximumLength: 16_384) { [weak self] data, _, isComplete, error in
            var request = received
            if let data { request.append(data) }
            guard error == nil, request.count < 32_768 else { return connection.cancel() }
            if let body = Self.body(of: request) {
                self?.handle(body)
                let reply = "HTTP/1.1 204 No Content\r\nConnection: close\r\nContent-Length: 0\r\n\r\n"
                connection.send(content: Data(reply.utf8), completion: .contentProcessed { _ in connection.cancel() })
            } else if isComplete {
                connection.cancel()
            } else {
                self?.read(connection, request)
            }
        }
    }

    /** The request's body once all of it has arrived, or nil while it's still coming. */
    private static func body(of request: Data) -> Data? {
        guard let end = request.range(of: Data("\r\n\r\n".utf8)) else { return nil }
        let headers = String(decoding: request[..<end.lowerBound], as: UTF8.self).lowercased()
        let length = headers.split(separator: "\r\n")
            .first { $0.hasPrefix("content-length:") }
            .flatMap { Int($0.dropFirst("content-length:".count).trimmingCharacters(in: .whitespaces)) } ?? 0
        let body = request[end.upperBound...]
        return body.count >= length ? Data(body.prefix(length)) : nil
    }

    private func handle(_ body: Data) {
        guard let message = (try? JSONSerialization.jsonObject(with: body)) as? [String: Any],
              message["type"] as? String == "react",
              let key = message["key"] as? String, PetArt.reactions[key] != nil else { return }
        var reaction: [String: Any] = ["type": "react", "key": key]
        if let vars = message["vars"] as? [String: String] { reaction["vars"] = vars }
        onReact(reaction)
    }
}
