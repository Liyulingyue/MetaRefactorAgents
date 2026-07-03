use anyhow::{Context, Result};
use clap::Clap;
use reqwest::Client;
use serde::{Deserialize, Serialize};
use serde_json::json;
use std::collections::HashMap;
use std::env;
use std::io::{BufRead, BufReader, Write};
use std::path::Path;
use std::process::{Command, Stdio};
use std::sync::Arc;

mod config;
mod tools;

use config::Config;
use tools::Tool;

#[derive(Debug, Clone)]
struct Message {
    role: String,
    content: String,
    #[allow(dead_code)]
    tool_calls: Option<Vec<ToolCall>>,
    tool_call_id: Option<String>,
    name: Option<String>,
}

#[derive(Debug, Clone, Deserialize)]
pub struct ToolCall {
    id: String,
    #[serde(rename = "type")]
    typ: String,
    function: FunctionDef,
}

#[derive(Debug, Clone, Deserialize)]
pub struct FunctionDef {
    name: String,
    arguments: String,
}

#[derive(Debug, Clone, Serialize)]
struct ChatMessage {
    role: String,
    content: String,
    #[serde(skip_serializing_if = "Option::is_none")]
    tool_calls: Option<Vec<serde_json::Value>>,
    #[serde(skip_serializing_if = "Option::is_none")]
    tool_call_id: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    name: Option<String>,
}

impl From<Message> for ChatMessage {
    fn from(m: Message) -> Self {
        ChatMessage {
            role: m.role,
            content: m.content,
            tool_calls: None,
            tool_call_id: m.tool_call_id,
            name: m.name,
        }
    }
}

struct Agent {
    config: Config,
    client: Client,
    tools: Vec<Tool>,
    messages: Vec<Message>,
}

impl Agent {
    fn new(config: Config) -> Self {
        Agent {
            config,
            client: Client::new(),
            tools: tools::get_tools(),
            messages: Vec::new(),
        }
    }

    fn system_prompt() -> String {
        r#"You are a versatile and autonomous general-purpose agent (MRA).
MRA (MetaRefactorAgents) is a system where agents collaborate to refactor code across the fleet.

CORE PROTOCOL:
1. ANALYZE: Understand the mission and identify the target.
2. ACTION: Leverage standard tools to read files, execute commands, and write code.
3. RESPONSE: Provide clear, concise reports on your actions."#.to_string()
    }

    async fn chat(&mut self, user_input: &str) -> Result<String> {
        self.messages.push(Message {
            role: "user".to_string(),
            content: user_input.to_string(),
            tool_calls: None,
            tool_call_id: None,
            name: None,
        });

        loop {
            let response = self.send_request().await?;

            if let Some(tool_calls) = response.tool_calls {
                for tc in tool_calls {
                    let tool_call_id = tc.id.clone();
                    let function_name = tc.function.name.clone();
                    let arguments = tc.function.arguments.clone();

                    self.messages.push(Message {
                        role: "assistant".to_string(),
                        content: response.content.clone(),
                        tool_calls: Some(vec![tc]),
                        tool_call_id: None,
                        name: None,
                    });

                    let result = self.execute_tool(&function_name, &arguments).await;

                    self.messages.push(Message {
                        role: "tool".to_string(),
                        content: result,
                        tool_calls: None,
                        tool_call_id: Some(tool_call_id),
                        name: Some(function_name),
                    });
                }
            } else {
                let content = response.content.clone();
                self.messages.push(Message {
                    role: "assistant".to_string(),
                    content: content.clone(),
                    tool_calls: None,
                    tool_call_id: None,
                    name: None,
                });
                return Ok(content);
            }
        }
    }

    async fn send_request(&self) -> Result<Response> {
        let mut chat_messages: Vec<ChatMessage> = vec![ChatMessage {
            role: "system".to_string(),
            content: Self::system_prompt(),
        }];
        chat_messages.extend(self.messages.iter().cloned().map(ChatMessage::from));

        let tool_schemas: Vec<serde_json::Value> = self
            .tools
            .iter()
            .map(|t| t.to_schema())
            .collect();

        let body = json!({
            "model": self.config.model,
            "messages": chat_messages,
            "tools": tool_schemas,
            "tool_choice": "auto"
        });

        let resp = self
            .client
            .post(format!("{}/chat/completions", self.config.base_url))
            .header("Authorization", format!("Bearer {}", self.config.api_key))
            .json(&body)
            .send()
            .await?
            .error_for_status()
            .context("OpenAI API request failed")?;

        #[derive(Deserialize)]
        struct ApiResponse {
            choices: Vec<ApiChoice>,
        }
        #[derive(Deserialize)]
        struct ApiChoice {
            message: Response,
        }
        #[derive(Debug, Clone, Deserialize)]
        struct Response {
            content: String,
            #[serde(default)]
            tool_calls: Option<Vec<ToolCall>>,
        }

        let api_resp: ApiResponse = resp.json().await?;
        api_resp
            .choices
            .first()
            .map(|c| c.message.clone())
            .context("No response from API")
    }

    async fn execute_tool(&self, name: &str, args: &str) -> String {
        if let Some(tool) = self.tools.iter().find(|t| t.name() == name) {
            let args_map: HashMap<String, serde_json::Value> =
                serde_json::from_str(args).unwrap_or_default();
            match tool.execute(args_map).await {
                Ok(result) => result,
                Err(e) => format!("Error: {}", e),
            }
        } else {
            format!("Unknown tool: {}", name)
        }
    }
}

#[tokio::main]
async fn main() -> Result<()> {
    let config = Config::load();

    println!("===========================================");
    println!("  MRA Agent - Lightweight CLI Agent");
    println!("===========================================");
    println!();
    println!("Model: {}", config.model);
    println!("Base URL: {}", config.base_url);
    println!("API Key: {}...", &config.api_key[..8.min(config.api_key.len())]);
    println!();
    println!("Type your message and press Enter to chat.");
    println!("Type 'exit' or 'quit' to end the session.");
    println!("Type 'clear' to clear conversation history.");
    println!("===========================================");
    println!();

    let mut agent = Agent::new(config);

    loop {
        print!("> ");
        std::io::stdout().flush()?;

        let mut input = String::new();
        let stdin = std::io::stdin();
        let mut handle = stdin.lock();
        if handle.read_line(&mut input)? == 0 {
            break;
        }

        let input = input.trim();
        if input.is_empty() {
            continue;
        }

        match input.to_lowercase().as_str() {
            "exit" | "quit" => {
                println!("Goodbye!");
                break;
            }
            "clear" => {
                agent.messages.clear();
                println!("Conversation history cleared.");
                continue;
            }
            _ => {}
        }

        match agent.chat(input).await {
            Ok(response) => {
                println!("\n[Agent] {}\n", response);
            }
            Err(e) => {
                eprintln!("\n[Error] {}\n", e);
            }
        }
    }

    Ok(())
}
