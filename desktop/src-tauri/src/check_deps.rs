// Linux system dependency checker
// This runs at app startup to verify required libraries are installed

use std::process::Command;

#[cfg(target_os = "linux")]
pub fn check_system_dependencies() -> Result<(), String> {
    let required_libs = vec![
        ("libwebkit2gtk-4.1", "WebKitGTK (UI framework)"),
    ];

    let optional_libs = vec![
        ("tesseract", "Tesseract (receipt scanning)"),
    ];

    let mut missing_required = Vec::new();
    let mut missing_optional = Vec::new();

    // Check required libraries
    for (lib_name, lib_display) in &required_libs {
        if !check_library_installed(lib_name) {
            missing_required.push(format!("{} ({})", lib_display, lib_name));
        }
    }

    // Check optional libraries
    for (lib_name, lib_display) in &optional_libs {
        if !check_library_installed(lib_name) {
            missing_optional.push(format!("{} ({})", lib_display, lib_name));
        }
    }

    if !missing_required.is_empty() {
        let libs = missing_required.join(", ");
        return Err(format!(
            "Missing required system libraries: {}\n\n\
             Please install them using your package manager:\n\
             - Debian/Ubuntu: sudo apt-get install libwebkit2gtk-4.1-0\n\
             - Fedora/RHEL: sudo dnf install webkit2gtk4.1\n\
             - Arch Linux: sudo pacman -S webkit2gtk-4.1",
            libs
        ));
    }

    if !missing_optional.is_empty() {
        eprintln!(
            "Warning: Optional libraries not found: {}",
            missing_optional.join(", ")
        );
        eprintln!("Receipt scanning will not work. Install Tesseract if needed:");
        eprintln!("  - Debian/Ubuntu: sudo apt-get install tesseract-ocr");
        eprintln!("  - Fedora/RHEL: sudo dnf install tesseract");
        eprintln!("  - Arch Linux: sudo pacman -S tesseract");
    }

    Ok(())
}

#[cfg(not(target_os = "linux"))]
pub fn check_system_dependencies() -> Result<(), String> {
    Ok(())
}

#[cfg(target_os = "linux")]
fn check_library_installed(lib_name: &str) -> bool {
    // Try to find library using ldconfig
    let output = Command::new("ldconfig")
        .arg("-p")
        .output()
        .map(|o| String::from_utf8_lossy(&o.stdout).to_string())
        .unwrap_or_default();

    output.contains(lib_name) || check_pkg_config(lib_name)
}

#[cfg(target_os = "linux")]
fn check_pkg_config(lib_name: &str) -> bool {
    Command::new("pkg-config")
        .arg("--exists")
        .arg(lib_name)
        .status()
        .map(|status| status.success())
        .unwrap_or(false)
}

#[cfg(not(target_os = "linux"))]
fn check_library_installed(_lib_name: &str) -> bool {
    true
}
