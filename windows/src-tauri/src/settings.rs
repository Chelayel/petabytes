//! What the person chose, kept as JSON in the app's config folder (%APPDATA%\com.chelayel.petabytes).

use serde::{Deserialize, Serialize};
use std::path::PathBuf;

#[derive(Clone, Serialize, Deserialize)]
#[serde(default, rename_all = "camelCase")]
pub struct Settings {
    pub pet: String,
    /// Empty for the pet's own name.
    pub name: String,
    /// 1.0 is the VS Code size.
    pub zoom: f64,
    pub visible: bool,
    /// Steps aside while a game, a video or a presentation is full screen.
    pub hide_in_full_screen: bool,
    /// Reacts to what Claude Code is doing (the Petabytes add-on for Claude Code tells it).
    pub claude_code: bool,
    /// Seconds since 1970, set on first run.
    pub first_run: u64,
    /// When to next ask for a star or a coffee; u64::MAX once answered.
    pub ask_for_support_after: u64,
    pub last_update_check: u64,
    /// The newest version already offered unasked, so each is offered once.
    pub offered_update: String,
}

impl Default for Settings {
    fn default() -> Self {
        Settings {
            pet: "turtle".into(),
            name: String::new(),
            zoom: 1.3,
            visible: true,
            hide_in_full_screen: true,
            claude_code: true,
            first_run: 0,
            ask_for_support_after: 0,
            last_update_check: 0,
            offered_update: String::new(),
        }
    }
}

impl Settings {
    pub fn load(path: &PathBuf) -> Settings {
        let mut settings: Settings = std::fs::read_to_string(path)
            .ok()
            .and_then(|text| serde_json::from_str(&text).ok())
            .unwrap_or_default();
        if settings.first_run == 0 {
            settings.first_run = now();
        }
        settings
    }

    pub fn save(&self, path: &PathBuf) {
        if let Some(dir) = path.parent() {
            let _ = std::fs::create_dir_all(dir);
        }
        if let Ok(text) = serde_json::to_string_pretty(self) {
            let _ = std::fs::write(path, text);
        }
    }
}

pub fn now() -> u64 {
    std::time::SystemTime::now()
        .duration_since(std::time::UNIX_EPOCH)
        .map(|d| d.as_secs())
        .unwrap_or(0)
}
