// Build script for Python bindings
use std::process::Command;

fn main() {
    // Compile the Rust library with Python feature
    let status = Command::new("cargo")
        .args(&["build", "--release", "--features", "python"])
        .status()
        .expect("Failed to compile Rust library");
    
    if !status.success() {
        panic!("Failed to compile Rust library");
    }
    
    println!("cargo:rerun-if-changed=src/lib.rs");
    println!("cargo:rerun-if-changed=src/py.rs");
}
