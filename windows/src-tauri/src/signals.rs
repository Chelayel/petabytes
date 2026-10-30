//! What the pet learns from Windows, none of it behind a permission: which app is in front (by its file name), how
//! long since the last key or mouse input (never which key), the battery, and whether something is full screen.

/// The screen's area minus the taskbar, in physical pixels: left, top, right, bottom.
pub fn work_area() -> Option<(i32, i32, i32, i32)> {
    imp::work_area()
}

/// The front window's program, lower case, like "code.exe".
pub fn front_app() -> Option<String> {
    imp::front_app()
}

/// Milliseconds since the last key press or mouse movement anywhere.
pub fn idle_ms() -> u32 {
    imp::idle_ms()
}

pub struct Power {
    pub plugged_in: bool,
    /// None without a battery.
    pub percent: Option<u8>,
    pub saver: bool,
}

pub fn power() -> Option<Power> {
    imp::power()
}

/// A game, a video or a presentation has the screen (Windows' own "busy" states).
pub fn full_screen() -> bool {
    imp::full_screen()
}

/// The reaction (in pets.json) to bringing an app to the front, by its program's file name.
pub fn reaction_for(app: &str) -> Option<&'static str> {
    const APPS: &[(&str, &[&str])] = &[
        ("terminal", &["windowsterminal.exe", "cmd.exe", "powershell.exe", "pwsh.exe", "wezterm-gui.exe", "alacritty.exe",
                       "warp.exe", "mintty.exe", "hyper.exe", "tabby.exe", "conemu64.exe"]),
        ("ai", &["claude.exe", "chatgpt.exe", "perplexity.exe", "copilot.exe"]),
        ("ide", &["code.exe", "code - insiders.exe", "cursor.exe", "windsurf.exe", "idea64.exe", "pycharm64.exe",
                  "webstorm64.exe", "rider64.exe", "clion64.exe", "goland64.exe", "phpstorm64.exe", "rubymine64.exe",
                  "studio64.exe", "devenv.exe", "sublime_text.exe", "zed.exe", "notepad++.exe", "fleet.exe"]),
        ("meeting", &["zoom.exe", "ms-teams.exe", "teams.exe", "webex.exe"]),
        ("music", &["spotify.exe", "tidal.exe", "itunes.exe", "applemusic.exe"]),
        ("browser", &["chrome.exe", "msedge.exe", "firefox.exe", "brave.exe", "opera.exe", "vivaldi.exe", "arc.exe", "zen.exe"]),
        ("chat", &["slack.exe", "discord.exe", "whatsapp.exe", "telegram.exe", "signal.exe", "messenger.exe"]),
        ("mail", &["outlook.exe", "olk.exe", "thunderbird.exe", "mailbird.exe"]),
        ("design", &["figma.exe", "photoshop.exe", "illustrator.exe", "blender.exe", "krita.exe", "inkscape.exe", "canva.exe"]),
        ("notes", &["notion.exe", "obsidian.exe", "onenote.exe", "winword.exe", "logseq.exe"]),
        ("game", &["steam.exe", "epicgameslauncher.exe", "battle.net.exe", "minecraftlauncher.exe", "riotclientux.exe"]),
        ("video", &["vlc.exe", "mpv.exe", "mpc-hc64.exe", "potplayermini64.exe"]),
        ("activity", &["taskmgr.exe"]),
        ("docker", &["docker desktop.exe"]),
        ("database", &["dbeaver.exe", "datagrip64.exe", "ssms.exe", "tableplus.exe", "heidisql.exe"]),
        ("api", &["postman.exe", "insomnia.exe", "bruno.exe"]),
        ("settings", &["systemsettings.exe"]),
        ("appStore", &["winstore.app.exe"]),
        ("passwords", &["1password.exe", "bitwarden.exe", "keepassxc.exe"]),
        ("screenshot", &["snippingtool.exe", "sharex.exe"]),
    ];
    APPS.iter().find(|(_, apps)| apps.contains(&app)).map(|(key, _)| *key)
}

#[cfg(windows)]
mod imp {
    use super::Power;
    use std::ffi::c_void;
    use windows_sys::Win32::Foundation::{CloseHandle, RECT};
    use windows_sys::Win32::System::Power::{GetSystemPowerStatus, SYSTEM_POWER_STATUS};
    use windows_sys::Win32::System::SystemInformation::GetTickCount;
    use windows_sys::Win32::System::Threading::{
        OpenProcess, QueryFullProcessImageNameW, PROCESS_NAME_WIN32, PROCESS_QUERY_LIMITED_INFORMATION,
    };
    use windows_sys::Win32::UI::Input::KeyboardAndMouse::{GetLastInputInfo, LASTINPUTINFO};
    use windows_sys::Win32::UI::Shell::{
        SHQueryUserNotificationState, QUNS_BUSY, QUNS_PRESENTATION_MODE, QUNS_RUNNING_D3D_FULL_SCREEN,
    };
    use windows_sys::Win32::UI::WindowsAndMessaging::{
        GetForegroundWindow, GetWindowThreadProcessId, SystemParametersInfoW, SPI_GETWORKAREA,
    };

    pub fn work_area() -> Option<(i32, i32, i32, i32)> {
        let mut r = RECT { left: 0, top: 0, right: 0, bottom: 0 };
        let ok = unsafe { SystemParametersInfoW(SPI_GETWORKAREA, 0, &mut r as *mut RECT as *mut c_void, 0) };
        (ok != 0 && r.right > r.left).then_some((r.left, r.top, r.right, r.bottom))
    }

    pub fn front_app() -> Option<String> {
        unsafe {
            let window = GetForegroundWindow();
            if window.is_null() {
                return None;
            }
            let mut pid = 0u32;
            GetWindowThreadProcessId(window, &mut pid);
            let process = OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, 0, pid);
            if process.is_null() {
                return None;
            }
            let mut path = [0u16; 1024];
            let mut len = path.len() as u32;
            let ok = QueryFullProcessImageNameW(process, PROCESS_NAME_WIN32, path.as_mut_ptr(), &mut len);
            CloseHandle(process);
            if ok == 0 {
                return None;
            }
            let path = String::from_utf16_lossy(&path[..len as usize]);
            path.rsplit('\\').next().map(|name| name.to_lowercase())
        }
    }

    pub fn idle_ms() -> u32 {
        let mut info = LASTINPUTINFO { cbSize: std::mem::size_of::<LASTINPUTINFO>() as u32, dwTime: 0 };
        unsafe {
            if GetLastInputInfo(&mut info) == 0 {
                return u32::MAX;
            }
            GetTickCount().wrapping_sub(info.dwTime)
        }
    }

    pub fn power() -> Option<Power> {
        let mut status: SYSTEM_POWER_STATUS = unsafe { std::mem::zeroed() };
        if unsafe { GetSystemPowerStatus(&mut status) } == 0 {
            return None;
        }
        // 128: no battery; 255: unknown.
        let battery = status.BatteryFlag & 128 == 0 && status.BatteryLifePercent <= 100;
        Some(Power {
            plugged_in: status.ACLineStatus == 1,
            percent: battery.then_some(status.BatteryLifePercent),
            saver: status.SystemStatusFlag == 1,
        })
    }

    pub fn full_screen() -> bool {
        let mut state = 0;
        let ok = unsafe { SHQueryUserNotificationState(&mut state) } >= 0;
        ok && (state == QUNS_BUSY || state == QUNS_RUNNING_D3D_FULL_SCREEN || state == QUNS_PRESENTATION_MODE)
    }
}

/// Elsewhere (building on a Mac or Linux to check the code), Windows never answers.
#[cfg(not(windows))]
mod imp {
    use super::Power;
    pub fn work_area() -> Option<(i32, i32, i32, i32)> { None }
    pub fn front_app() -> Option<String> { None }
    pub fn idle_ms() -> u32 { u32::MAX }
    pub fn power() -> Option<Power> { None }
    pub fn full_screen() -> bool { false }
}
