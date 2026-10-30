//! Petabytes for Windows: a pet that walks along the top of your taskbar and reacts to what your PC is doing.
//! It's web/pet.html, the page VS Code and the Mac app show, in a see-through window that lets clicks through
//! everywhere but the pet. Its menu is on the tray icon and on the pet, by right-click.

#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

mod link;
mod settings;
mod signals;
mod updates;

use serde_json::{json, Value};
use settings::{now, Settings};
use std::path::PathBuf;
use std::sync::{Mutex, MutexGuard, OnceLock};
use std::time::Duration;
use tauri::menu::{CheckMenuItem, IsMenuItem, Menu, MenuItem, PredefinedMenuItem, Submenu};
use tauri::tray::TrayIconBuilder;
use tauri::{AppHandle, Manager, PhysicalPosition, PhysicalSize, WebviewUrl, WebviewWindowBuilder, Wry};
use tauri_plugin_autostart::{MacosLauncher, ManagerExt as _};
use tauri_plugin_dialog::{DialogExt, MessageDialogButtons};
use tauri_plugin_opener::OpenerExt;

const PETS: &str = include_str!("../../../web/pets.json");
const COFFEE: &str = "https://buymeacoffee.com/chelayel";
const GITHUB: &str = "https://github.com/Chelayel/petabytes";
const SIZES: [(&str, f64); 3] = [("Small", 1.0), ("Medium", 1.3), ("Large", 1.7)];
/// The strip the pet walks in, above the taskbar, in page pixels before the size is applied.
const SEA_HEIGHT: f64 = 150.0;
const DAY: u64 = 24 * 60 * 60;

/**
 Runs in the pet's page before its own script: the page talks to VS Code through acquireVsCodeApi(), so the app
 provides one. It also hides the name label, drops the glow (a filter redrawn every frame is the most expensive
 thing on the page), reports where the pet is (for click-through) and opens the menu on right-click.
 */
const PET_SHIM: &str = r#"
(() => {
  const invoke = (cmd, args) => window.__TAURI_INTERNALS__.invoke(cmd, args);
  window.acquireVsCodeApi = () => ({ postMessage: (msg) => invoke("from_page", { msg }), getState: () => undefined, setState: () => {} });
  addEventListener("DOMContentLoaded", () => {
    const style = document.createElement("style");
    style.textContent = ".name { display: none; } #pet svg { filter: none; } html, body { background: transparent !important; }";
    document.head.appendChild(style);
    const pet = document.getElementById("pet");
    setInterval(() => {
      const r = pet.getBoundingClientRect();
      invoke("rect", { x: r.left, y: r.top, w: r.width, h: r.height });
    }, 100);
    pet.addEventListener("contextmenu", (e) => { e.preventDefault(); invoke("menu"); });
  });
})();
"#;

/// The same for Choose a Pet (web/picker.html), which only tells the app which pet was picked.
const PICKER_SHIM: &str = r#"
window.acquireVsCodeApi = () => ({
  postMessage: (msg) => window.__TAURI_INTERNALS__.invoke("from_page", { msg }), getState: () => undefined, setState: () => {},
});
"#;

fn catalog() -> &'static Value {
    static CATALOG: OnceLock<Value> = OnceLock::new();
    CATALOG.get_or_init(|| serde_json::from_str(PETS).expect("pets.json doesn't parse"))
}

struct Inner {
    settings: Settings,
    path: PathBuf,
    /// The page has loaded; until then messages wait in `queued`.
    ready: bool,
    queued: Vec<String>,
    /// Where the pet is in the page (CSS pixels): x, y, width, height.
    rect: [f64; 4],
    /// Battery saver is on: fewer frames, no antics.
    quiet: bool,
    hidden_for_full_screen: bool,
    update: Option<updates::Release>,
}

struct AppState(Mutex<Inner>);

fn state(app: &AppHandle) -> MutexGuard<'_, Inner> {
    app.state::<AppState>().inner().0.lock().unwrap_or_else(|e| e.into_inner())
}

fn mutate(app: &AppHandle, change: impl FnOnce(&mut Settings)) {
    let mut s = state(app);
    change(&mut s.settings);
    s.settings.save(&s.path);
}

fn pet_name(settings: &Settings) -> String {
    if !settings.name.is_empty() {
        return settings.name.clone();
    }
    catalog()["pets"][&settings.pet]["name"].as_str().unwrap_or("Pet").to_string()
}

// ---- The page ---------------------------------------------------------------

/// Hands the page a message, as pet.html's receive() expects: config, react, feed, active and so on.
fn send(app: &AppHandle, message: Value) {
    let script = format!("window.petabytes && window.petabytes.receive({message})");
    {
        let mut s = state(app);
        if !s.ready {
            s.queued.push(script);
            return;
        }
    }
    if let Some(window) = app.get_webview_window("pet") {
        let _ = window.eval(&script);
    }
}

fn react(app: &AppHandle, key: &str, vars: Value) {
    send(app, json!({ "type": "react", "key": key, "vars": vars }));
}

fn configure(app: &AppHandle) {
    let (pet, name, quiet) = {
        let s = state(app);
        (s.settings.pet.clone(), s.settings.name.clone(), s.quiet)
    };
    // 30 frames a second is plenty for a pet; 20 on battery saver, which also stops its antics.
    send(app, json!({ "type": "config", "pet": pet, "name": name, "ground": true, "fps": if quiet { 20 } else { 30 }, "quiet": quiet }));
}

#[tauri::command]
fn from_page(app: AppHandle, window: tauri::Window, msg: Value) {
    match (window.label(), msg["type"].as_str()) {
        ("pet", Some("ready")) => {
            let queued = {
                let mut s = state(&app);
                s.ready = true;
                std::mem::take(&mut s.queued)
            };
            configure(&app);
            if let Some(pet) = app.get_webview_window("pet") {
                for script in queued {
                    let _ = pet.eval(&script);
                }
            }
        }
        ("picker", Some("choose")) => {
            if let Some(id) = msg["id"].as_str() {
                choose(&app, id);
            }
        }
        _ => {}
    }
}

#[tauri::command]
fn rect(app: AppHandle, x: f64, y: f64, w: f64, h: f64) {
    state(&app).rect = [x, y, w, h];
}

#[tauri::command]
async fn menu(app: AppHandle, window: tauri::Window) {
    if let Ok(menu) = build_menu(&app) {
        let _ = window.popup_menu(&menu);
    }
}

// ---- Where it lives -----------------------------------------------------------

/// A strip as wide as the screen whose bottom edge is the top of the taskbar: pet.html stands the pet on it.
fn place(app: &AppHandle) {
    let Some(window) = app.get_webview_window("pet") else { return };
    let zoom = state(app).settings.zoom;
    let scale = window.scale_factor().unwrap_or(1.0);
    let (left, _, right, bottom) = signals::work_area()
        .or_else(|| {
            let monitor = window.primary_monitor().ok().flatten()?;
            let (p, s) = (monitor.position(), monitor.size());
            Some((p.x, p.y, p.x + s.width as i32, p.y + s.height as i32))
        })
        .unwrap_or((0, 0, 1280, 720));
    let height = (SEA_HEIGHT * zoom * scale).round() as i32;
    let _ = window.set_size(PhysicalSize::new((right - left).max(1) as u32, height as u32));
    let _ = window.set_position(PhysicalPosition::new(left, bottom - height));
    let _ = window.set_zoom(zoom);
}

fn set_visible(app: &AppHandle, visible: bool) {
    mutate(app, |s| s.visible = visible);
    let hidden_for_full_screen = state(app).hidden_for_full_screen;
    if let Some(window) = app.get_webview_window("pet") {
        let _ = if visible && !hidden_for_full_screen { window.show() } else { window.hide() };
    }
}

/// Clicks go through the window everywhere but on the pet. Checked 15 times a second while the pointer is near
/// the strip, 4 times a second otherwise.
fn click_through(app: AppHandle) {
    std::thread::spawn(move || {
        let mut over = false;
        loop {
            let mut wait = 250;
            let found = (|| {
                let window = app.get_webview_window("pet")?;
                let cursor = window.cursor_position().ok()?;
                let origin = window.outer_position().ok()?;
                let size = window.outer_size().ok()?;
                let scale = window.scale_factor().ok()?;
                let (r, zoom) = {
                    let s = state(&app);
                    (s.rect, s.settings.zoom)
                };
                let f = scale * zoom;
                let (x, y) = (cursor.x - origin.x as f64, cursor.y - origin.y as f64);
                let near = y >= -60.0 && y <= size.height as f64 + 60.0;
                let on_pet = x >= r[0] * f && x <= (r[0] + r[2]) * f && y >= r[1] * f && y <= (r[1] + r[3]) * f;
                Some((window, near, on_pet))
            })();
            if let Some((window, near, on_pet)) = found {
                if near {
                    wait = 66;
                }
                if on_pet != over {
                    over = on_pet;
                    let _ = window.set_ignore_cursor_events(!on_pet);
                }
            }
            std::thread::sleep(Duration::from_millis(wait));
        }
    });
}

// ---- Choosing -------------------------------------------------------------------

fn show_picker(app: &AppHandle) {
    if let Some(picker) = app.get_webview_window("picker") {
        let _ = picker.set_focus();
        return;
    }
    let current = Value::from(state(app).settings.pet.clone());
    let script = format!("window.__petabytesCurrent = {current};\n{PICKER_SHIM}");
    let _ = WebviewWindowBuilder::new(app, "picker", WebviewUrl::App("picker.html".into()))
        .title("Choose a Pet")
        .inner_size(820.0, 620.0)
        .center()
        .initialization_script(&script)
        .build();
}

fn choose(app: &AppHandle, id: &str) {
    if catalog()["pets"].get(id).is_none() {
        return;
    }
    mutate(app, |s| {
        s.pet = id.to_string();
        s.name.clear();
    });
    configure(app);
    if !state(app).settings.visible {
        set_visible(app, true);
    }
    refresh_menu(app);
}

// ---- The menu -------------------------------------------------------------------

fn build_menu(app: &AppHandle) -> tauri::Result<Menu<Wry>> {
    let (s, update) = {
        let st = state(app);
        (st.settings.clone(), st.update.clone())
    };
    let login = app.autolaunch().is_enabled().unwrap_or(false);
    let sizes = SIZES
        .iter()
        .map(|(label, zoom)| {
            CheckMenuItem::with_id(app, format!("size:{zoom}"), *label, true, (s.zoom - zoom).abs() < 0.01, None::<&str>)
        })
        .collect::<tauri::Result<Vec<_>>>()?;
    let size_items: Vec<&dyn IsMenuItem<Wry>> = sizes.iter().map(|item| item as &dyn IsMenuItem<Wry>).collect();
    let size = Submenu::with_items(app, "Size", true, &size_items)?;
    let update_item = match &update {
        Some(release) => MenuItem::with_id(app, "update", format!("Update to {}…", release.version), true, None::<&str>)?,
        None => MenuItem::with_id(app, "check", "Check for Updates…", true, None::<&str>)?,
    };
    Menu::with_items(
        app,
        &[
            &MenuItem::with_id(app, "feed", format!("Feed {}", pet_name(&s)), true, None::<&str>)?,
            &MenuItem::with_id(app, "choose", "Choose Pet…", true, None::<&str>)?,
            &PredefinedMenuItem::separator(app)?,
            &size,
            &MenuItem::with_id(app, "visible", if s.visible { "Hide Pet" } else { "Show Pet" }, true, None::<&str>)?,
            &PredefinedMenuItem::separator(app)?,
            &CheckMenuItem::with_id(app, "claude", "React to Claude Code", true, s.claude_code, None::<&str>)?,
            &CheckMenuItem::with_id(app, "fullscreen", "Hide in Full Screen", true, s.hide_in_full_screen, None::<&str>)?,
            &CheckMenuItem::with_id(app, "login", "Open at Login", true, login, None::<&str>)?,
            &PredefinedMenuItem::separator(app)?,
            &update_item,
            &MenuItem::with_id(app, "star", "Star on GitHub…", true, None::<&str>)?,
            &MenuItem::with_id(app, "coffee", "Buy Me a Coffee…", true, None::<&str>)?,
            &PredefinedMenuItem::separator(app)?,
            &MenuItem::with_id(app, "quit", "Quit Petabytes", true, None::<&str>)?,
        ],
    )
}

fn refresh_menu(app: &AppHandle) {
    if let (Some(tray), Ok(menu)) = (app.tray_by_id("main"), build_menu(app)) {
        let _ = tray.set_menu(Some(menu));
    }
}

fn handle_menu(app: &AppHandle, id: &str) {
    match id {
        "feed" => {
            let visible = state(app).settings.visible;
            if !visible {
                set_visible(app, true);
            }
            send(app, json!({ "type": "feed", "key": "feed" }));
        }
        // On Windows, a window built inside a menu handler can deadlock: build it on another thread.
        "choose" => {
            let app = app.clone();
            std::thread::spawn(move || show_picker(&app));
        }
        "visible" => {
            let visible = state(app).settings.visible;
            set_visible(app, !visible);
        }
        "claude" => mutate(app, |s| s.claude_code = !s.claude_code),
        "fullscreen" => mutate(app, |s| s.hide_in_full_screen = !s.hide_in_full_screen),
        "login" => {
            let autolaunch = app.autolaunch();
            let _ = if autolaunch.is_enabled().unwrap_or(false) { autolaunch.disable() } else { autolaunch.enable() };
        }
        "check" => check_for_updates(app, false),
        "update" => {
            let update = state(app).update.clone();
            if let Some(release) = update {
                open(app, &release.download);
            }
        }
        "star" => {
            open(app, GITHUB);
            mutate(app, |s| s.ask_for_support_after = u64::MAX);
        }
        "coffee" => {
            open(app, COFFEE);
            mutate(app, |s| s.ask_for_support_after = u64::MAX);
        }
        "quit" => app.exit(0),
        _ => {
            if let Some(zoom) = id.strip_prefix("size:").and_then(|z| z.parse::<f64>().ok()) {
                mutate(app, |s| s.zoom = zoom);
                place(app);
            }
        }
    }
    refresh_menu(app);
}

fn open(app: &AppHandle, url: &str) {
    let _ = app.opener().open_url(url, None::<&str>);
}

fn tell(app: &AppHandle, title: &str, text: &str) {
    app.dialog().message(text).title(title).show(|_| {});
}

// ---- Now and then ---------------------------------------------------------------

/// Once a day (and from Check for Updates…): a newer release is offered once, then waits in the menu.
fn check_for_updates(app: &AppHandle, quietly: bool) {
    let app = app.clone();
    std::thread::spawn(move || {
        let current = app.package_info().version.to_string();
        mutate(&app, |s| s.last_update_check = now());
        match updates::latest(&current) {
            Err(error) => {
                // Offline, or GitHub busy: try again within the hour.
                mutate(&app, |s| s.last_update_check = 0);
                if !quietly {
                    tell(&app, "Couldn't check for updates", &format!("GitHub didn't answer: {error}"));
                }
            }
            Ok(None) => {
                state(&app).update = None;
                if !quietly {
                    tell(&app, "Petabytes is up to date", &format!("You have the latest version, {current}."));
                }
            }
            Ok(Some(release)) => {
                state(&app).update = Some(release.clone());
                refresh_menu(&app);
                let offered = state(&app).settings.offered_update.clone();
                if quietly && offered == release.version {
                    return;
                }
                mutate(&app, |s| s.offered_update = release.version.clone());
                let handle = app.clone();
                let download = release.download.clone();
                app.dialog()
                    .message(format!("You have {current}. Download the new version? Run the installer once it's downloaded, and your pet comes right back."))
                    .title(format!("Petabytes {} is available", release.version))
                    .buttons(MessageDialogButtons::OkCancelCustom("Download".into(), "Later".into()))
                    .show(move |ok| {
                        if ok {
                            open(&handle, &download);
                        }
                    });
            }
        }
    });
}

/// After a week with the pet, asks once for a coffee. Not Now asks again in a month; the coffee, or the star and
/// coffee in the menu, and it never asks again.
fn ask_for_support_if_due(app: &AppHandle) {
    let s = state(app).settings.clone();
    let due = if s.ask_for_support_after == 0 { s.first_run + 7 * DAY } else { s.ask_for_support_after };
    if now() < due || signals::full_screen() {
        return;
    }
    mutate(app, |s| s.ask_for_support_after = now() + 30 * DAY);
    let handle = app.clone();
    app.dialog()
        .message("Petabytes is free and made by one person. If your pet makes your day a little better, a coffee keeps new pets coming (and a star on GitHub, in the menu, helps others find it).")
        .title(format!("Enjoying {}?", pet_name(&s)))
        .buttons(MessageDialogButtons::OkCancelCustom("Buy Me a Coffee".into(), "Not Now".into()))
        .show(move |ok| {
            if ok {
                open(&handle, COFFEE);
                mutate(&handle, |s| s.ask_for_support_after = u64::MAX);
            }
        });
}

/// What Windows tells the pet, every 2 seconds: someone's there, which app is in front, the battery, full screen.
/// Each is one cheap call; the hourly work (updates, the support ask) rides along.
fn watch(app: AppHandle) {
    std::thread::spawn(move || {
        let mut front = String::new();
        let mut was_low = false;
        let mut plugged_in: Option<bool> = None;
        let mut area = signals::work_area();
        // The first hourly round a minute after launch.
        let mut last_hourly = now().saturating_sub(3600 - 60);
        loop {
            std::thread::sleep(Duration::from_secs(2));
            if signals::idle_ms() < 2_500 {
                send(&app, json!({ "type": "active" }));
            }
            if let Some(app_name) = signals::front_app() {
                if app_name != front {
                    if let Some(key) = signals::reaction_for(&app_name) {
                        react(&app, key, json!({}));
                    }
                    front = app_name;
                }
            }
            if let Some(power) = signals::power() {
                if let Some(percent) = power.percent {
                    let low = !power.plugged_in && percent <= 20;
                    if low && !was_low {
                        react(&app, "batteryLow", json!({ "percent": format!("{percent}%") }));
                    }
                    was_low = low;
                    if plugged_in == Some(false) && power.plugged_in {
                        react(&app, "charging", json!({}));
                    }
                    plugged_in = Some(power.plugged_in);
                }
                let changed = {
                    let mut s = state(&app);
                    let changed = s.quiet != power.saver;
                    s.quiet = power.saver;
                    changed
                };
                if changed {
                    configure(&app);
                }
            }
            check_full_screen(&app);
            // The taskbar moved, or the screen changed.
            let now_area = signals::work_area();
            if now_area != area {
                area = now_area;
                place(&app);
            }
            if now().saturating_sub(last_hourly) >= 3600 {
                last_hourly = now();
                if now().saturating_sub(state(&app).settings.last_update_check) > DAY {
                    check_for_updates(&app, true);
                }
                ask_for_support_if_due(&app);
            }
        }
    });
}

fn check_full_screen(app: &AppHandle) {
    let (enabled, visible, was) = {
        let s = state(app);
        (s.settings.hide_in_full_screen, s.settings.visible, s.hidden_for_full_screen)
    };
    let full = enabled && signals::full_screen();
    if full == was {
        return;
    }
    state(app).hidden_for_full_screen = full;
    if let Some(window) = app.get_webview_window("pet") {
        let _ = if full { window.hide() } else if visible { window.show() } else { Ok(()) };
    }
}

fn main() {
    tauri::Builder::default()
        // A second launch feeds the pet instead of starting another.
        .plugin(tauri_plugin_single_instance::init(|app, _args, _cwd| {
            send(app, json!({ "type": "feed", "key": "feed" }));
        }))
        .plugin(tauri_plugin_autostart::init(MacosLauncher::LaunchAgent, None))
        .plugin(tauri_plugin_dialog::init())
        .plugin(tauri_plugin_opener::init())
        .invoke_handler(tauri::generate_handler![from_page, rect, menu])
        .on_menu_event(|app, event| handle_menu(app, event.id().as_ref()))
        .setup(|app| {
            let handle = app.handle().clone();
            let path = app.path().app_config_dir()?.join("settings.json");
            let settings = Settings::load(&path);
            settings.save(&path);
            let visible = settings.visible;
            app.manage(AppState(Mutex::new(Inner {
                settings,
                path,
                ready: false,
                queued: Vec::new(),
                rect: [0.0; 4],
                quiet: false,
                hidden_for_full_screen: false,
                update: None,
            })));

            let window = WebviewWindowBuilder::new(app, "pet", WebviewUrl::App("index.html".into()))
                .title("Petabytes")
                .transparent(true)
                .decorations(false)
                .shadow(false)
                .always_on_top(true)
                .skip_taskbar(true)
                .resizable(false)
                .focused(false)
                .visible(false)
                .initialization_script(PET_SHIM)
                .build()?;
            place(&handle);
            let _ = window.set_ignore_cursor_events(true);
            if visible {
                window.show()?;
            }

            TrayIconBuilder::with_id("main")
                .icon(app.default_window_icon().cloned().expect("the app has an icon"))
                .tooltip("Petabytes")
                .menu(&build_menu(&handle)?)
                .build(app)?;

            let known = |key: &str| catalog()["reactions"].get(key).is_some();
            let linked = handle.clone();
            link::start(known, move |reaction| {
                if state(&linked).settings.claude_code {
                    send(&linked, reaction);
                }
            });
            watch(handle.clone());
            click_through(handle);
            Ok(())
        })
        .build(tauri::generate_context!())
        .expect("Petabytes couldn't start")
        .run(|_, event| {
            // Closing Choose a Pet isn't quitting.
            if let tauri::RunEvent::ExitRequested { api, code: None, .. } = event {
                api.prevent_exit();
            }
        });
}
