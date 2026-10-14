import os
from typing import List, Optional
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
import yaml
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def coerce_value(key: str, value):
    if key in ["port", "workers"]:
        try:
            return int(value)
        except ValueError:
            return value
    elif key == "debug":
        if isinstance(value, bool):
            return value
        return str(value).lower() in ["true", "1", "yes", "on"]
    else:
        return str(value)

@app.get("/effective-config")
def get_effective_config(set: Optional[List[str]] = Query(None)):
    # Layer 1: Defaults (Hardcoded)
    config = {
        "port": 8000,
        "workers": 1,
        "debug": False,
        "log_level": "info",
        "api_key": "default-secret-000"
    }

    # Layer 2: config.development.yaml
    yaml_path = "config.development.yaml"
    if os.path.exists(yaml_path):
        try:
            with open(yaml_path, "r") as f:
                yaml_data = yaml.safe_load(f)
                if yaml_data:
                    for k, v in yaml_data.items():
                        config[k] = coerce_value(k, v)
        except Exception:
            pass

    # Layer 3: .env file & Aliases (NUM_WORKERS -> workers)
    if os.getenv("APP_PORT"):
        config["port"] = coerce_value("port", os.getenv("APP_PORT"))
    if os.getenv("APP_API_KEY"):
        config["api_key"] = coerce_value("api_key", os.getenv("APP_API_KEY"))
    if os.getenv("NUM_WORKERS"):
        config["workers"] = coerce_value("workers", os.getenv("NUM_WORKERS"))

    # Layer 4: OS env vars (APP_* prefix)
    if os.getenv("APP_PORT"):
        config["port"] = coerce_value("port", os.getenv("APP_PORT"))
    if os.getenv("APP_WORKERS"):
        config["workers"] = coerce_value("workers", os.getenv("APP_WORKERS"))
    if os.getenv("APP_DEBUG"):
        config["debug"] = coerce_value("debug", os.getenv("APP_DEBUG"))
    if os.getenv("APP_LOG_LEVEL"):
        config["log_level"] = coerce_value("log_level", os.getenv("APP_LOG_LEVEL"))
    if os.getenv("APP_API_KEY"):
        config["api_key"] = coerce_value("api_key", os.getenv("APP_API_KEY"))

    # Layer 5: CLI Overrides via query params (?set=key=value)
    if set:
        for item in set:
            if "=" in item:
                parts = item.split("=", 1)
                k = parts[0].strip()
                v = parts[1].strip()
                config[k] = coerce_value(k, v)

    # Type coercion enforcement
    config["port"] = coerce_value("port", config["port"])
    config["workers"] = coerce_value("workers", config["workers"])
    config["debug"] = coerce_value("debug", config["debug"])
    config["log_level"] = coerce_value("log_level", config["log_level"])

    # Secret Masking
    response_config = config.copy()
    response_config["api_key"] = "****"

    return response_config