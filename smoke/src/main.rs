use duckdb::Connection;

fn main() -> Result<(), Box<dyn std::error::Error>> {
    // This crate deliberately does NOT enable duckdb-rs `bundled`. If this
    // executable links and runs, the staged archive is sufficient for the
    // exact consumption mode AnyDatas will use.
    let connection = Connection::open_in_memory()?;
    let version: String = connection.query_row("SELECT version()", [], |row| row.get(0))?;
    let answer: i64 = connection.query_row("SELECT sum(i) FROM range(7) t(i)", [], |row| row.get(0))?;
    assert_eq!(answer, 21);
    assert!(version.contains("1.5.4"), "unexpected DuckDB version: {version}");
    println!("linked smoke test passed with {version}");
    Ok(())
}
