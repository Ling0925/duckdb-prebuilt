use duckdb::Connection;

fn main() -> Result<(), Box<dyn std::error::Error>> {
    // Force the bundled libduckdb-sys path to compile and link all the way into
    // a real executable. The release workflow then extracts the native archive
    // from Cargo's libduckdb-sys OUT_DIR.
    let connection = Connection::open_in_memory()?;
    let version: String = connection.query_row("SELECT version()", [], |row| row.get(0))?;
    let answer: i64 = connection.query_row("SELECT 40 + 2", [], |row| row.get(0))?;
    assert_eq!(answer, 42);
    assert!(version.contains("1.5.4"), "unexpected DuckDB version: {version}");
    println!("built {version}");
    Ok(())
}
