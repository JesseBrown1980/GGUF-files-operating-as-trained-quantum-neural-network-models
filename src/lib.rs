//! GGUF files operating as trained qutrit virtual quantum neural networks. Exact, integer only.
#![forbid(unsafe_code)]
#![deny(clippy::float_arithmetic)]

pub mod bigint;
pub mod cyclo;
pub mod eisenstein;
pub mod gguf_model;
pub mod gguf_read;
pub mod hbp;
pub mod qnn;
pub mod qutrit;
pub mod qutrit9;
pub mod real3;
pub mod sha256;
pub mod task;
pub mod train;
pub mod v2;
pub mod v4;
pub mod virtual_qnn;
pub mod ym_z3;
