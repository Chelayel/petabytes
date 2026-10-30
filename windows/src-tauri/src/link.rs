//! Lets Claude Code drive the pet: the Petabytes add-on for Claude Code posts what Claude is doing to this app on
//! 127.0.0.1, never over the network, as the Mac app takes it. Each request is one small JSON reaction,
//! {"type": "react", "key": "claudeDone"}; keys that pets.json doesn't know are ignored.

use serde_json::Value;
use std::io::{Read, Write};
use std::net::TcpListener;
use std::time::Duration;

/// Where the add-on finds the app; it's in the add-on too.
pub const PORT: u16 = 47_365;

/// Listens on its own thread; each reaction goes to `on_react`. Quietly does nothing if the port is taken.
pub fn start(known: impl Fn(&str) -> bool + Send + 'static, on_react: impl Fn(Value) + Send + 'static) {
    let Ok(listener) = TcpListener::bind(("127.0.0.1", PORT)) else { return };
    std::thread::spawn(move || {
        for stream in listener.incoming() {
            let Ok(mut stream) = stream else { continue };
            let _ = stream.set_read_timeout(Some(Duration::from_secs(2)));
            if let Some(body) = read_body(&mut stream) {
                let _ = stream.write_all(b"HTTP/1.1 204 No Content\r\nConnection: close\r\nContent-Length: 0\r\n\r\n");
                if let Ok(message) = serde_json::from_slice::<Value>(&body) {
                    let key = message["key"].as_str().unwrap_or_default();
                    if message["type"] == "react" && known(key) {
                        let mut reaction = serde_json::json!({ "type": "react", "key": key });
                        if message["vars"].is_object() {
                            reaction["vars"] = message["vars"].clone();
                        }
                        on_react(reaction);
                    }
                }
            }
        }
    });
}

/// Reads until the request is whole (headers, then Content-Length bytes of body), up to 32 KB.
fn read_body(stream: &mut impl Read) -> Option<Vec<u8>> {
    let mut request = Vec::new();
    let mut chunk = [0u8; 4096];
    loop {
        if let Some(end) = request.windows(4).position(|w| w == b"\r\n\r\n") {
            let headers = String::from_utf8_lossy(&request[..end]).to_lowercase();
            let length = headers
                .lines()
                .find_map(|line| line.strip_prefix("content-length:"))
                .and_then(|n| n.trim().parse::<usize>().ok())
                .unwrap_or(0);
            let body = &request[end + 4..];
            if body.len() >= length {
                return Some(body[..length].to_vec());
            }
        }
        let read = stream.read(&mut chunk).ok()?;
        if read == 0 || request.len() > 32_768 {
            return None;
        }
        request.extend_from_slice(&chunk[..read]);
    }
}
