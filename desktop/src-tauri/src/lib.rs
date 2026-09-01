use std::sync::Mutex;

use tauri::{Manager, RunEvent};
use tauri_plugin_dialog::DialogExt;
use tauri_plugin_shell::{process::CommandChild, ShellExt};

struct BackendProcess(Mutex<Option<CommandChild>>);

#[tauri::command]
async fn save_generated_file(app: tauri::AppHandle, file_name: String) -> Result<bool, String> {
    if std::path::Path::new(&file_name)
        .file_name()
        .and_then(|name| name.to_str())
        != Some(&file_name)
    {
        return Err("Invalid generated file name".into());
    }

    let source = app
        .path()
        .app_data_dir()
        .map_err(|error| error.to_string())?
        .join("exports")
        .join(&file_name);
    if !source.is_file() {
        return Err("Generated file no longer exists".into());
    }

    let extension = source
        .extension()
        .and_then(|value| value.to_str())
        .unwrap_or("");
    let destination = app
        .dialog()
        .file()
        .add_filter("Inventory Vault", &[extension])
        .set_file_name(&file_name)
        .blocking_save_file();
    let Some(destination) = destination else {
        return Ok(false);
    };
    let destination = destination.into_path().map_err(|error| error.to_string())?;
    std::fs::copy(source, destination).map_err(|error| error.to_string())?;
    Ok(true)
}

#[tauri::command]
async fn stage_restore(app: tauri::AppHandle) -> Result<bool, String> {
    let selected = app
        .dialog()
        .file()
        .add_filter("Inventory Vault backup", &["zip"])
        .blocking_pick_file();
    let Some(selected) = selected else {
        return Ok(false);
    };
    let source = selected.into_path().map_err(|error| error.to_string())?;
    if !source
        .extension()
        .and_then(|value| value.to_str())
        .is_some_and(|extension| extension.eq_ignore_ascii_case("zip"))
    {
        return Err("Select an Inventory Vault ZIP backup".into());
    }

    let app_data_dir = app
        .path()
        .app_data_dir()
        .map_err(|error| error.to_string())?;
    std::fs::create_dir_all(&app_data_dir).map_err(|error| error.to_string())?;
    let pending = app_data_dir.join("pending-restore.zip");
    let temporary = app_data_dir.join("pending-restore.tmp");
    std::fs::copy(source, &temporary).map_err(|error| error.to_string())?;
    let _ = std::fs::remove_file(&pending);
    std::fs::rename(temporary, pending).map_err(|error| error.to_string())?;
    Ok(true)
}

fn start_backend(app: &tauri::App) -> Result<CommandChild, Box<dyn std::error::Error>> {
    let app_data_dir = app.path().app_data_dir()?;
    let uploads_dir = app_data_dir.join("uploads");
    std::fs::create_dir_all(&uploads_dir)?;
    let database_path = app_data_dir
        .join("inventory.db")
        .to_string_lossy()
        .replace('\\', "/");

    let (_, child) = app
        .shell()
        .sidecar("inventory-vault-backend")?
        .env("DATABASE_URL", format!("sqlite:///{database_path}"))
        .env("STORAGE_DIR", uploads_dir)
        .env("REQUIRE_AUTHENTICATION", "false")
        .env("INVENTORY_VAULT_PORT", "8765")
        .spawn()?;

    Ok(child)
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    let app = tauri::Builder::default()
        .plugin(tauri_plugin_shell::init())
        .plugin(tauri_plugin_dialog::init())
        .plugin(tauri_plugin_process::init())
        .invoke_handler(tauri::generate_handler![save_generated_file, stage_restore])
        .setup(|app| {
            if cfg!(debug_assertions) {
                app.handle().plugin(
                    tauri_plugin_log::Builder::default()
                        .level(log::LevelFilter::Info)
                        .build(),
                )?;
            }

            let backend = start_backend(app)?;
            app.manage(BackendProcess(Mutex::new(Some(backend))));
            Ok(())
        })
        .build(tauri::generate_context!())
        .expect("error while building tauri application");

    app.run(|app_handle, event| {
        if let RunEvent::Exit = event {
            let process = app_handle.state::<BackendProcess>();
            if let Ok(mut backend) = process.0.lock() {
                if let Some(child) = backend.take() {
                    let _ = child.kill();
                }
            };
        }
    });
}
