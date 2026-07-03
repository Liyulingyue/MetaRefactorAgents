use anyhow::Result;
use async_trait::async_trait;
use serde::{Deserialize, Serialize};
use serde_json::Value;
use std::collections::HashMap;
use std::fs;
use std::io::Write;
use std::path::Path;
use std::process::Command;

#[async_trait::async_trait]
pub trait Tool {
    fn name(&self) -> &str;
    fn description(&self) -> &str;
    fn parameters(&self) -> Vec<Parameter>;
    fn to_schema(&self) -> Value {
        json!({
            "type": "function",
            "function": {
                "name": self.name(),
                "description": self.description(),
                "parameters": {
                    "type": "object",
                    "properties": {
                        for p in self.parameters() {
                            p.name.clone(): {
                                let mut obj = json!({"type": p.param_type});
                                if let Some(desc) = &p.description {
                                    obj["description"] = json!(desc);
                                }
                                obj
                            }
                        }
                    },
                    "required": self.parameters().iter().filter(|p| p.required).map(|p| p.name.clone()).collect::<Vec<_>>()
                }
            }
        })
    }
    async fn execute(&self, args: HashMap<String, Value>) -> Result<String>;
}

#[derive(Clone)]
pub struct ExecuteBashTool;

#[async_trait::async_trait]
impl Tool for ExecuteBashTool {
    fn name(&self) -> &str {
        "execute_bash"
    }
    fn description(&self) -> &str {
        "Execute a bash command in the terminal and return its output."
    }
    fn parameters(&self) -> Vec<Parameter> {
        vec![Parameter {
            name: "command".to_string(),
            param_type: "string".to_string(),
            description: Some("The bash command to run".to_string()),
            required: true,
        }]
    }
    async fn execute(&self, args: HashMap<String, Value>) -> Result<String> {
        let command = args
            .get("command")
            .and_then(|v| v.as_str())
            .unwrap_or("");

        let output = if cfg!(target_os = "windows") {
            Command::new("cmd")
                .args(["/C", command])
                .output()?
        } else {
            Command::new("sh")
                .args(["-c", command])
                .output()?
        };

        let stdout = String::from_utf8_lossy(&output.stdout);
        let stderr = String::from_utf8_lossy(&output.stderr);

        Ok(format!(
            "STDOUT:\n{}\nSTDERR:\n{}",
            stdout,
            stderr
        ))
    }
}

#[derive(Clone)]
pub struct WriteFileTool;

#[async_trait::async_trait]
impl Tool for WriteFileTool {
    fn name(&self) -> &str {
        "write_file"
    }
    fn description(&self) -> &str {
        "Write content to a file. Creates the file if it doesn't exist."
    }
    fn parameters(&self) -> Vec<Parameter> {
        vec![
            Parameter {
                name: "file_path".to_string(),
                param_type: "string".to_string(),
                description: Some("Path to the file".to_string()),
                required: true,
            },
            Parameter {
                name: "content".to_string(),
                param_type: "string".to_string(),
                description: Some("Content to write".to_string()),
                required: true,
            },
        ]
    }
    async fn execute(&self, args: HashMap<String, Value>) -> Result<String> {
        let file_path = args
            .get("file_path")
            .and_then(|v| v.as_str())
            .unwrap_or("");
        let content = args
            .get("content")
            .and_then(|v| v.as_str())
            .unwrap_or("");

        if let Some(parent) = Path::new(file_path).parent() {
            fs::create_dir_all(parent)?;
        }

        let mut file = fs::File::create(file_path)?;
        file.write_all(content.as_bytes())?;

        Ok(format!("Successfully wrote to {}", file_path))
    }
}

#[derive(Clone)]
pub struct ReadFileTool;

#[async_trait::async_trait]
impl Tool for ReadFileTool {
    fn name(&self) -> &str {
        "read_file"
    }
    fn description(&self) -> &str {
        "Read the entire content of a file."
    }
    fn parameters(&self) -> Vec<Parameter> {
        vec![Parameter {
            name: "file_path".to_string(),
            param_type: "string".to_string(),
            description: Some("Path to the file".to_string()),
            required: true,
        }]
    }
    async fn execute(&self, args: HashMap<String, Value>) -> Result<String> {
        let file_path = args
            .get("file_path")
            .and_then(|v| v.as_str())
            .unwrap_or("");

        let content = fs::read_to_string(file_path)?;
        Ok(content)
    }
}

#[derive(Clone)]
pub struct CallPeerAgentTool;

#[async_trait::async_trait]
impl Tool for CallPeerAgentTool {
    fn name(&self) -> &str {
        "call_peer_agent"
    }
    fn description(&self) -> &str {
        "Send a message to another agent via the gateway."
    }
    fn parameters(&self) -> Vec<Parameter> {
        vec![
            Parameter {
                name: "agent_id".to_string(),
                param_type: "string".to_string(),
                description: Some("Target agent ID".to_string()),
                required: true,
            },
            Parameter {
                name: "prompt".to_string(),
                param_type: "string".to_string(),
                description: Some("Task description".to_string()),
                required: true,
            },
        ]
    }
    async fn execute(&self, args: HashMap<String, Value>) -> Result<String> {
        let agent_id = args
            .get("agent_id")
            .and_then(|v| v.as_str())
            .unwrap_or("");
        let prompt = args
            .get("prompt")
            .and_then(|v| v.as_str())
            .unwrap_or("");

        let gateway_url =
            std::env::var("GATEWAY_URL").unwrap_or_else(|_| "http://localhost:8000".to_string());

        let client = reqwest::Client::new();
        let resp = client
            .post(format!("{}/api/agents/{}/agent/chat", gateway_url, agent_id))
            .json(&serde_json::json!({
                "prompt": prompt,
                "history": []
            }))
            .send()
            .await?;

        if resp.status().is_success() {
            let data: serde_json::Value = resp.json().await?;
            Ok(format!(
                "Response from {}:\n{}",
                agent_id,
                data.get("response").and_then(|v| v.as_str()).unwrap_or("")
            ))
        } else {
            Ok(format!(
                "Error calling {}: Status {}",
                agent_id,
                resp.status()
            ))
        }
    }
}

#[derive(Clone)]
pub struct ListPeersTool;

#[async_trait::async_trait]
impl Tool for ListPeersTool {
    fn name(&self) -> &str {
        "list_peers"
    }
    fn description(&self) -> &str {
        "List all active peer agents in the MRA system."
    }
    fn parameters(&self) -> Vec<Parameter> {
        vec![]
    }
    async fn execute(&self, _args: HashMap<String, Value>) -> Result<String> {
        let gateway_url =
            std::env::var("GATEWAY_URL").unwrap_or_else(|_| "http://localhost:8000".to_string());

        let client = reqwest::Client::new();
        let resp = client.get(format!("{}/api/agents", gateway_url)).send().await?;

        if resp.status().is_success() {
            let agents: Vec<serde_json::Value> = resp.json().await?;
            let peer_list: Vec<String> = agents
                .iter()
                .map(|a| {
                    format!(
                        "- ID: {} (Port: {})",
                        a.get("id").and_then(|v| v.as_str()).unwrap_or("unknown"),
                        a.get("port").and_then(|v| v.as_str()).unwrap_or("unknown")
                    )
                })
                .collect();
            Ok("Available Peer Agents:\n".to_string() + &peer_list.join("\n"))
        } else {
            Ok(format!("Error listing peers: {}", resp.status()))
        }
    }
}

#[derive(Clone)]
pub struct PublishToSharedTool;

#[async_trait::async_trait]
impl Tool for PublishToSharedTool {
    fn name(&self) -> &str {
        "publish_to_shared"
    }
    fn description(&self) -> &str {
        "Copy a file to the shared workspace for user access."
    }
    fn parameters(&self) -> Vec<Parameter> {
        vec![Parameter {
            name: "file_path".to_string(),
            param_type: "string".to_string(),
            description: Some("Path to the file to publish".to_string()),
            required: true,
        }]
    }
    async fn execute(&self, args: HashMap<String, Value>) -> Result<String> {
        let file_path = args
            .get("file_path")
            .and_then(|v| v.as_str())
            .unwrap_or("");

        if !Path::new(file_path).exists() {
            return Ok(format!("Error: File {} not found", file_path));
        }

        let agent_id = std::env::var("AGENT_ID").unwrap_or_else(|_| "agent".to_string());
        let filename = Path::new(file_path)
            .file_name()
            .and_then(|n| n.to_str())
            .unwrap_or("unknown");

        let shared_name = format!("{}_{}", agent_id, filename);
        let shared_dir = Path::new("..").join("shared_files");
        fs::create_dir_all(&shared_dir)?;
        let target = shared_dir.join(&shared_name);

        fs::copy(file_path, &target)?;

        Ok(format!(
            "Successfully published {} to shared area as {}",
            file_path, shared_name
        ))
    }
}

pub fn get_tools() -> Vec<Box<dyn Tool + Send + Sync>> {
    vec![
        Box::new(ExecuteBashTool),
        Box::new(WriteFileTool),
        Box::new(ReadFileTool),
        Box::new(CallPeerAgentTool),
        Box::new(ListPeersTool),
        Box::new(PublishToSharedTool),
    ]
}

#[derive(Clone)]
pub struct Parameter {
    pub name: String,
    pub param_type: String,
    pub description: Option<String>,
    pub required: bool,
}
