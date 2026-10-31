//! POST-HOC DIAGNOSTIC (after the v2 pilot; not a sealed verdict).
use gguf_qnn::qutrit9::{Net9, State9};
use gguf_qnn::sha256::digest;
use gguf_qnn::task::points;
use gguf_qnn::v2::{marginal, margins};
fn irr(s: &State9, q: usize) -> bool {
    marginal(s, q)
        .iter()
        .any(|x| !x.c[1].is_zero() || !x.c[2].is_zero())
}
fn main() {
    let (tr, _) = points();
    for layers in 1..=3usize {
        let params: Vec<i64> = (0..4 * 6 * layers)
            .map(|i| i64::from(digest(format!("V2SEED|0|{i}").as_bytes())[0] % 3))
            .collect();
        let net = Net9 {
            n: 6,
            layers,
            params,
        };
        let ms = margins(&net, &tr);
        let zero = ms.iter().filter(|m| m.is_zero()).count();
        let pos = ms.iter().filter(|m| m.sign() == Some(1)).count();
        let mut s = State9::basis(6, &[1, 2, 0, 1, 0, 2]);
        net.forward(&mut s);
        let per: Vec<u8> = (0..6).map(|q| u8::from(irr(&s, q))).collect();
        println!("DIAG|seed=SHA-V2-0|layers={layers}|train_points={}|margin_exactly_zero={zero}|margin_positive={pos}|irrational_marginal_by_qutrit_on_one_input={per:?}|json=0", tr.len());
    }
}
