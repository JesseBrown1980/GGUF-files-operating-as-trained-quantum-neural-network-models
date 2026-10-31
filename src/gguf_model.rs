//! A trained model as a GGUF v3 file: header keys (strings and u32) and int8 tensors.
//! Writer and reader, integer only.

pub enum Kv {
    Str(String),
    U32(u32),
}

pub struct Model {
    pub kv: Vec<(String, Kv)>,
    pub tensors: Vec<(String, Vec<i8>)>,
}

fn put_str(b: &mut Vec<u8>, s: &str) {
    b.extend_from_slice(&(s.len() as u64).to_le_bytes());
    b.extend_from_slice(s.as_bytes());
}

pub fn write(m: &Model) -> Vec<u8> {
    let mut b = b"GGUF".to_vec();
    b.extend_from_slice(&3u32.to_le_bytes());
    b.extend_from_slice(&(m.tensors.len() as u64).to_le_bytes());
    b.extend_from_slice(&(m.kv.len() as u64).to_le_bytes());
    for (k, v) in &m.kv {
        put_str(&mut b, k);
        match v {
            Kv::Str(s) => {
                b.extend_from_slice(&8u32.to_le_bytes());
                put_str(&mut b, s);
            }
            Kv::U32(x) => {
                b.extend_from_slice(&4u32.to_le_bytes());
                b.extend_from_slice(&x.to_le_bytes());
            }
        }
    }
    let mut off = 0u64;
    let mut offsets = Vec::new();
    for (name, data) in &m.tensors {
        put_str(&mut b, name);
        b.extend_from_slice(&1u32.to_le_bytes());
        b.extend_from_slice(&(data.len() as u64).to_le_bytes());
        b.extend_from_slice(&24u32.to_le_bytes()); // GGML I8
        b.extend_from_slice(&off.to_le_bytes());
        offsets.push(off);
        off += (data.len() as u64).div_ceil(32) * 32;
    }
    while b.len() % 32 != 0 {
        b.push(0);
    }
    for (_, data) in &m.tensors {
        b.extend(data.iter().map(|&x| x as u8));
        while b.len() % 32 != 0 {
            b.push(0);
        }
    }
    b
}

fn rd_u32(b: &[u8], o: &mut usize) -> Option<u32> {
    let s = b.get(*o..*o + 4)?;
    *o += 4;
    Some(u32::from_le_bytes([s[0], s[1], s[2], s[3]]))
}
fn rd_u64(b: &[u8], o: &mut usize) -> Option<u64> {
    let s = b.get(*o..*o + 8)?;
    *o += 8;
    let mut a = [0u8; 8];
    a.copy_from_slice(s);
    Some(u64::from_le_bytes(a))
}
fn rd_str(b: &[u8], o: &mut usize) -> Option<String> {
    let n = usize::try_from(rd_u64(b, o)?).ok()?;
    let s = b.get(*o..*o + n)?;
    *o += n;
    Some(String::from_utf8_lossy(s).into_owned())
}

pub fn read(b: &[u8]) -> Option<Model> {
    if b.get(0..4)? != b"GGUF" {
        return None;
    }
    let mut o = 4;
    if rd_u32(b, &mut o)? != 3 {
        return None;
    }
    let nt = rd_u64(b, &mut o)?;
    let nk = rd_u64(b, &mut o)?;
    let mut kv = Vec::new();
    for _ in 0..nk {
        let k = rd_str(b, &mut o)?;
        let v = match rd_u32(b, &mut o)? {
            8 => Kv::Str(rd_str(b, &mut o)?),
            4 => Kv::U32(rd_u32(b, &mut o)?),
            _ => return None,
        };
        kv.push((k, v));
    }
    let mut info = Vec::new();
    for _ in 0..nt {
        let name = rd_str(b, &mut o)?;
        if rd_u32(b, &mut o)? != 1 {
            return None;
        }
        let len = usize::try_from(rd_u64(b, &mut o)?).ok()?;
        if rd_u32(b, &mut o)? != 24 {
            return None;
        }
        let off = usize::try_from(rd_u64(b, &mut o)?).ok()?;
        info.push((name, len, off));
    }
    let base = o.div_ceil(32) * 32;
    let mut tensors = Vec::new();
    for (name, len, off) in info {
        let s = b.get(base + off..base + off + len)?;
        tensors.push((name, s.iter().map(|&x| x as i8).collect()));
    }
    Some(Model { kv, tensors })
}

impl Model {
    pub fn str(&self, key: &str) -> Option<&str> {
        self.kv.iter().find_map(|(k, v)| match v {
            Kv::Str(s) if k == key => Some(s.as_str()),
            _ => None,
        })
    }
    pub fn u32(&self, key: &str) -> Option<u32> {
        self.kv.iter().find_map(|(k, v)| match v {
            Kv::U32(x) if k == key => Some(*x),
            _ => None,
        })
    }
    pub fn tensor(&self, name: &str) -> Option<&[i8]> {
        self.tensors
            .iter()
            .find(|(n, _)| n == name)
            .map(|(_, t)| t.as_slice())
    }
}
