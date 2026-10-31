//! GGUF files operating as trained qutrit virtual quantum neural networks. Exact, integer only.
#![forbid(unsafe_code)]
#![deny(clippy::float_arithmetic)]

pub mod eisenstein;
pub mod gguf_model;
pub mod gguf_read;
pub mod hbp;
pub mod qnn;
pub mod qutrit;
pub mod sha256;
pub mod task;
pub mod train;
pub mod virtual_qnn;
