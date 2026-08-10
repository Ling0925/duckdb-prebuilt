use std::env;

fn main() {
    let target_os = env::var("CARGO_CFG_TARGET_OS").expect("CARGO_CFG_TARGET_OS");
    match target_os.as_str() {
        // Linux/macOS normally obtain these through the duckdb.pc file staged
        // beside the archive. Emitting them here as well makes the smoke test
        // independent of pkg-config availability and documents the final link
        // contract explicitly.
        "linux" => {
            println!("cargo:rustc-link-lib=dylib=stdc++");
            println!("cargo:rustc-link-lib=dylib=m");
            println!("cargo:rustc-link-lib=dylib=dl");
            println!("cargo:rustc-link-lib=dylib=pthread");
        }
        "macos" => {
            println!("cargo:rustc-link-lib=dylib=c++");
        }
        // libduckdb-sys only emits these automatically for its bundled path.
        // The linked prebuilt path therefore needs to add them at the final
        // Rust link step. AnyDatas will mirror this target configuration.
        "windows" => {
            println!("cargo:rustc-link-lib=dylib=ws2_32");
            println!("cargo:rustc-link-lib=dylib=rstrtmgr");
            println!("cargo:rustc-link-lib=dylib=bcrypt");
        }
        other => panic!("unsupported smoke-test target OS: {other}"),
    }
}
