//! Finds out whether a newer Petabytes is out, from the project's GitHub releases. The app then offers the
//! installer for download (Windows has no signature here to check it by, so it doesn't install it unasked).

use serde_json::Value;

#[derive(Clone)]
pub struct Release {
    pub version: String,
    /// The Windows installer, or the release page when there isn't one.
    pub download: String,
}

const LATEST: &str = "https://api.github.com/repos/Chelayel/petabytes/releases/latest";

pub fn latest(current: &str) -> Result<Option<Release>, String> {
    let json: Value = ureq::get(LATEST)
        .set("Accept", "application/vnd.github+json")
        .set("User-Agent", &format!("Petabytes/{current}"))
        .timeout(std::time::Duration::from_secs(20))
        .call()
        .map_err(|e| e.to_string())?
        .into_json()
        .map_err(|e| e.to_string())?;
    let Some(tag) = json["tag_name"].as_str() else { return Ok(None) };
    let version = tag.trim_start_matches('v').to_string();
    if !is_newer(&version, current) {
        return Ok(None);
    }
    let installer = json["assets"].as_array().and_then(|assets| {
        assets.iter().filter_map(|a| a["browser_download_url"].as_str()).find(|url| url.ends_with("-setup.exe"))
    });
    let page = json["html_url"].as_str().unwrap_or("https://github.com/Chelayel/petabytes/releases/latest");
    Ok(Some(Release { version, download: installer.unwrap_or(page).to_string() }))
}

/// 1.10.0 is newer than 1.9.2: compared number by number.
pub fn is_newer(version: &str, than: &str) -> bool {
    let parse = |v: &str| v.split('.').map(|n| n.parse::<u64>().unwrap_or(0)).collect::<Vec<_>>();
    let (a, b) = (parse(version), parse(than));
    for i in 0..a.len().max(b.len()) {
        let (x, y) = (a.get(i).copied().unwrap_or(0), b.get(i).copied().unwrap_or(0));
        if x != y {
            return x > y;
        }
    }
    false
}
