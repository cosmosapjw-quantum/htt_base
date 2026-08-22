use serde::de::{DeserializeOwned, MapAccess, SeqAccess, Visitor};
use serde::{Deserialize, Deserializer, Serialize};
use serde_json::{Map, Number, Value};
use sha2::{Digest, Sha256};
use std::fmt;

struct StrictValue(Value);

impl<'de> Deserialize<'de> for StrictValue {
    fn deserialize<D>(deserializer: D) -> Result<Self, D::Error>
    where
        D: Deserializer<'de>,
    {
        struct StrictVisitor;

        impl<'de> Visitor<'de> for StrictVisitor {
            type Value = StrictValue;

            fn expecting(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
                formatter.write_str("finite JSON with no duplicate object keys")
            }

            fn visit_bool<E>(self, value: bool) -> Result<Self::Value, E> {
                Ok(StrictValue(Value::Bool(value)))
            }

            fn visit_i64<E>(self, value: i64) -> Result<Self::Value, E> {
                Ok(StrictValue(Value::Number(Number::from(value))))
            }

            fn visit_u64<E>(self, value: u64) -> Result<Self::Value, E> {
                Ok(StrictValue(Value::Number(Number::from(value))))
            }

            fn visit_f64<E>(self, value: f64) -> Result<Self::Value, E>
            where
                E: serde::de::Error,
            {
                Number::from_f64(value)
                    .map(Value::Number)
                    .map(StrictValue)
                    .ok_or_else(|| E::custom("non-finite JSON number"))
            }

            fn visit_str<E>(self, value: &str) -> Result<Self::Value, E>
            where
                E: serde::de::Error,
            {
                if !value.is_ascii() {
                    return Err(E::custom("non-ASCII JSON string"));
                }
                Ok(StrictValue(Value::String(value.to_owned())))
            }

            fn visit_string<E>(self, value: String) -> Result<Self::Value, E>
            where
                E: serde::de::Error,
            {
                self.visit_str(&value)
            }

            fn visit_none<E>(self) -> Result<Self::Value, E> {
                Ok(StrictValue(Value::Null))
            }

            fn visit_unit<E>(self) -> Result<Self::Value, E> {
                Ok(StrictValue(Value::Null))
            }

            fn visit_some<D>(self, deserializer: D) -> Result<Self::Value, D::Error>
            where
                D: Deserializer<'de>,
            {
                StrictValue::deserialize(deserializer)
            }

            fn visit_seq<A>(self, mut sequence: A) -> Result<Self::Value, A::Error>
            where
                A: SeqAccess<'de>,
            {
                let mut values = Vec::new();
                while let Some(value) = sequence.next_element::<StrictValue>()? {
                    values.push(value.0);
                }
                Ok(StrictValue(Value::Array(values)))
            }

            fn visit_map<A>(self, mut access: A) -> Result<Self::Value, A::Error>
            where
                A: MapAccess<'de>,
            {
                let mut values = Map::new();
                while let Some(key) = access.next_key::<String>()? {
                    if !key.is_ascii() {
                        return Err(serde::de::Error::custom("non-ASCII JSON key"));
                    }
                    if values.contains_key(&key) {
                        return Err(serde::de::Error::custom(format!(
                            "duplicate JSON key {key:?}"
                        )));
                    }
                    let value = access.next_value::<StrictValue>()?;
                    values.insert(key, value.0);
                }
                Ok(StrictValue(Value::Object(values)))
            }
        }

        deserializer.deserialize_any(StrictVisitor)
    }
}

pub(crate) fn canonical_bytes<T: Serialize>(value: &T) -> Result<Vec<u8>, String> {
    let normalized =
        serde_json::to_value(value).map_err(|error| format!("JSON normalize failed: {error}"))?;
    let raw =
        serde_json::to_vec(&normalized).map_err(|error| format!("JSON encode failed: {error}"))?;
    if !raw.is_ascii() {
        return Err("canonical JSON must be ASCII".to_owned());
    }
    Ok(raw)
}

pub(crate) fn parse_canonical<T>(raw: &[u8], label: &str) -> Result<T, String>
where
    T: DeserializeOwned + Serialize,
{
    let strict = parse_strict_value(raw, label)?;
    let normalized = canonical_bytes(&strict)?;
    if normalized != raw {
        return Err(format!(
            "{label} bytes are not sorted compact canonical JSON"
        ));
    }
    serde_json::from_value(strict)
        .map_err(|error| format!("{label} schema validation failed: {error}"))
}

fn parse_strict_value(raw: &[u8], label: &str) -> Result<Value, String> {
    if !raw.is_ascii() {
        return Err(format!("{label} must be ASCII"));
    }
    let mut deserializer = serde_json::Deserializer::from_slice(raw);
    let strict = StrictValue::deserialize(&mut deserializer)
        .map_err(|error| format!("{label} is not strict JSON: {error}"))?;
    deserializer
        .end()
        .map_err(|error| format!("{label} has trailing bytes: {error}"))?;
    Ok(strict.0)
}

pub(crate) fn parse_strict<T>(raw: &[u8], label: &str) -> Result<T, String>
where
    T: DeserializeOwned,
{
    serde_json::from_value(parse_strict_value(raw, label)?)
        .map_err(|error| format!("{label} schema validation failed: {error}"))
}

pub(crate) fn sha256_identity(raw: &[u8]) -> String {
    format!("sha256:{}", hex::encode(Sha256::digest(raw)))
}

pub(crate) fn content_id<T: Serialize>(value: &T) -> Result<String, String> {
    Ok(sha256_identity(&canonical_bytes(value)?))
}

pub(crate) fn require_sha256(value: &str, field: &str) -> Result<(), String> {
    let Some(raw) = value.strip_prefix("sha256:") else {
        return Err(format!("{field} is not a sha256 identity"));
    };
    if raw.len() != 64
        || !raw
            .bytes()
            .all(|byte| byte.is_ascii_hexdigit() && !byte.is_ascii_uppercase())
    {
        return Err(format!("{field} is not lowercase sha256"));
    }
    Ok(())
}

pub(crate) fn require_git_object(value: &str, field: &str) -> Result<(), String> {
    if !matches!(value.len(), 40 | 64)
        || !value
            .bytes()
            .all(|byte| byte.is_ascii_hexdigit() && !byte.is_ascii_uppercase())
    {
        return Err(format!("{field} is not a lowercase Git object id"));
    }
    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;
    use serde::{Deserialize, Serialize};

    #[derive(Debug, Deserialize, Serialize)]
    #[serde(deny_unknown_fields)]
    struct Row {
        a: u64,
        b: String,
    }

    #[test]
    fn rejects_duplicate_unknown_nonascii_and_noncanonical_json() {
        for raw in [
            br#"{"a":1,"a":1,"b":"x"}"#.as_slice(),
            br#"{"a":1,"b":"x","c":2}"#.as_slice(),
            br#"{ "a": 1, "b": "x" }"#.as_slice(),
        ] {
            assert!(parse_canonical::<Row>(raw, "row").is_err());
        }
        assert!(parse_canonical::<Row>("{\"a\":1,\"b\":\"é\"}".as_bytes(), "row").is_err());
        assert!(parse_canonical::<Row>(br#"{"a":1,"b":"x"}"#, "row").is_ok());
    }
}
