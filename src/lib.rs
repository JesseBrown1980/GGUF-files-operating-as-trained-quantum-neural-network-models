//! GGUF files operating as trained qutrit virtual quantum neural networks. Exact, integer only.
#![forbid(unsafe_code)]
#![deny(clippy::float_arithmetic)]

pub mod bigint;
pub mod cyclo;
pub mod eisenstein;
pub mod gfix;
pub mod gguf_model;
pub mod gguf_read;
pub mod google_qsim;
pub mod hbp;
pub mod pixels;
pub mod qnn;
pub mod qutrit;
pub mod qutrit9;
pub mod real3;
pub mod sha256;
pub mod spatial12b;
pub mod specialists;
pub mod task;
pub mod torus;
pub mod train;
pub mod v10;
pub mod v11;
pub mod v2;
pub mod v4;
pub mod v5;
pub mod v6;
pub mod v7;
pub mod v8;
pub mod v9;
pub mod virtual_qnn;
pub mod ym_z3;
