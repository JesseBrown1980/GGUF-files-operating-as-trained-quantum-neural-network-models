//! stripes-read-a --point ID --call I [--side PATH] < dump: one aggregate block, or one STOP row and exit 3.

use std::io::{BufReader, Write};

fn main() {
    std::panic::set_hook(Box::new(|info| {
        let msg = stripes_read_a::clean(&info.to_string());
        let row = format!(
            "STOP|reader={}|reader_version={}|reason=panic|detail={msg}|json=0\n",
            stripes_read_a::READER,
            stripes_read_a::READER_VERSION
        );
        let _ = std::io::stdout().write_all(row.as_bytes());
        let _ = std::io::stderr().write_all(row.as_bytes());
    }));
    let args: Vec<String> = std::env::args().skip(1).collect();
    let stdin = std::io::stdin();
    let rep = stripes_read_a::run(&args, BufReader::with_capacity(1 << 20, stdin.lock()));
    let mut out = std::io::stdout().lock();
    if out
        .write_all(rep.out.as_bytes())
        .and_then(|_| out.flush())
        .is_err()
    {
        std::process::exit(5);
    }
    if rep.code != 0 {
        let _ = std::io::stderr().write_all(rep.out.as_bytes());
    }
    std::process::exit(rep.code);
}
