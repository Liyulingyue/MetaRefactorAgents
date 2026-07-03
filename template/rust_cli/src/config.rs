use anyhow::Result;
use clap::Clap;
use std::env;

#[derive(Debug, Clone)]
pub struct Config {
    pub api_key: String,
    pub base_url: String,
    pub model: String,
}

impl Config {
    pub fn load() -> Self {
        if let Ok(api_key) = env::var("OPENAI_API_KEY") {
            return Config {
                api_key,
                base_url: env::var("OPENAI_BASE_URL")
                    .unwrap_or_else(|_| "https://api.openai.com/v1".to_string()),
                model: env::var("OPENAI_MODEL_NAME")
                    .unwrap_or_else(|_| "gpt-4o".to_string()),
            };
        }

        Config::parse()
    }

    fn parse() -> Self {
        let opts = Opts::parse();

        Config {
            api_key: opts.api_key,
            base_url: opts.base_url.unwrap_or_else(|| {
                env::var("OPENAI_BASE_URL")
                    .unwrap_or_else(|_| "https://api.openai.com/v1".to_string())
            }),
            model: opts.model.unwrap_or_else(|| {
                env::var("OPENAI_MODEL_NAME")
                    .unwrap_or_else(|_| "gpt-4o".to_string())
            }),
        }
    }
}

#[derive(Clap)]
#[clap(name = "agent")]
struct Opts {
    #[clap(long, env = "OPENAI_API_KEY")]
    api_key: String,

    #[clap(long, env = "OPENAI_BASE_URL")]
    base_url: Option<String>,

    #[clap(long, env = "OPENAI_MODEL_NAME")]
    model: Option<String>,
}
