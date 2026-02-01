import os
import time

import numpy as np
import torch

from lerobot.policies.pi0.modeling_pi0 import PI0Policy

if os.environ.get("DEBUG") == "1":
    import debugpy

    print("Waiting for debugger attach on port 5678...")
    debugpy.listen(("0.0.0.0", 5678))
    debugpy.wait_for_client()
    print("Debugger attached!")


def get_dummy_observation(
    policy: PI0Policy, device: str | torch.device, batch_size: int = 1
) -> dict[str, torch.Tensor]:
    from lerobot.utils.constants import OBS_LANGUAGE_ATTENTION_MASK, OBS_LANGUAGE_TOKENS

    print(f"DEBUG: Policy Input Features: {policy.config.input_features}")
    observation = {}
    for name, feature in policy.config.input_features.items():
        if isinstance(feature, dict):
            shape = (batch_size, *feature["shape"])
            # dtype = feature.get("dtype")
        else:
            shape = (batch_size, *feature.shape)
            # dtype = feature.dtype

        print(
            f"DEBUG: Generating dummy input for {name}, shape={shape},"
            f" type={getattr(feature, 'type', 'N/A')}"
        )
        # if dtype == "video":
        #     # Image/Video inputs: random tensors [B, C, H, W]
        observation[name] = torch.randn(shape, device=device)
        # else:
        #     # State/Actoin inputs: random floats
        #     observation[name] = torch.randn(shape, device=device)

    # Check for language inputs and add them if missing
    if OBS_LANGUAGE_TOKENS not in observation:
        print(f"DEBUG: Adding missing {OBS_LANGUAGE_TOKENS}")
        # Assuming tokenizer_max_length is available in config,
        # otherwise default to 48 (standard for PI0)
        max_length = getattr(policy.config, "tokenizer_max_length", 48)
        observation[OBS_LANGUAGE_TOKENS] = torch.randint(
            0, 1000, (batch_size, max_length), device=device, dtype=torch.long
        )

    if OBS_LANGUAGE_ATTENTION_MASK not in observation:
        print(f"DEBUG: Adding missing {OBS_LANGUAGE_ATTENTION_MASK}")
        # Assuming tokenizer_max_length is available in config, otherwise default to 48
        max_length = getattr(policy.config, "tokenizer_max_length", 48)
        observation[OBS_LANGUAGE_ATTENTION_MASK] = torch.ones(
            (batch_size, max_length), device=device, dtype=torch.long
        )

    return observation


def benchmark() -> None:
    # Use the expected model ID.
    # NOTE: You might need 'lerobot/pi0-base'
    # or similar if 'lerobot/pi0' is not the exact ID.
    policy_name = "lerobot/pi0"
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"Running benchmark for {policy_name} on {device}")

    # Load policy
    print("Loading policy (this may take a while to download)...")
    start_load = time.time()
    try:
        # 1. Download config to handle extra keys (workaround for config mismatch)
        import dataclasses
        import json

        from huggingface_hub import hf_hub_download

        from lerobot.policies.pi0.configuration_pi0 import PI0Config

        config_path = hf_hub_download(repo_id=policy_name, filename="config.json")
        with open(config_path, "r") as f:
            config_dict = json.load(f)

        # 2. Filter keys that are valid for PI0Config
        valid_keys = {f.name for f in dataclasses.fields(PI0Config)}
        filtered_config_dict = {k: v for k, v in config_dict.items() if k in valid_keys}

        # 2.5 Convert input_features/output_features from dicts to PolicyFeature objects
        # 2.5 Convert input_features/output_features from dicts to PolicyFeature objects
        # The JSON config has dicts, but the code expects objects (dataclasses)
        from lerobot.configs.types import FeatureType, PolicyFeature

        def dict_to_policy_feature(v):
            if isinstance(v, dict):
                # Convert type string to Enum
                if "type" in v and isinstance(v["type"], str):
                    v["type"] = FeatureType(v["type"])
                return PolicyFeature(**v)
            return v

        if "input_features" in filtered_config_dict:
            filtered_config_dict["input_features"] = {
                k: dict_to_policy_feature(v)
                for k, v in filtered_config_dict["input_features"].items()
            }
        if "output_features" in filtered_config_dict:
            filtered_config_dict["output_features"] = {
                k: dict_to_policy_feature(v)
                for k, v in filtered_config_dict["output_features"].items()
            }

        # 3. Create config and load policy
        config = PI0Config(**filtered_config_dict)
        policy = PI0Policy.from_pretrained(policy_name, config=config)

    except OSError as e:
        print(f"Error loading model: {e}")
        print(
            "Tip: If this is a gated model, "
            "make sure you are logged in via `huggingface-cli login`."
        )
        return
    except Exception as e:
        print(f"An unexpected error occurred during loading: {e}")
        return

    policy.to(device)
    policy.eval()
    print(f"Policy loaded in {time.time() - start_load:.2f}s")

    # Prepare dummy input (on CPU to measure transfer time)
    print("Preparing dummy inputs (on CPU)...")
    try:
        # Pass "cpu" explicitly to simulate real inputs coming from host/camera
        observation = get_dummy_observation(policy, "cpu")
    except Exception as e:
        print(f"Error creating dummy inputs: {e}")
        return

    print("Starting warmup (10 iterations)...")
    try:
        with torch.inference_mode():
            for _ in range(10):
                policy.select_action(observation)
                if device == "cuda":
                    torch.cuda.synchronize()
    except Exception as e:
        print(f"Error during warmup: {e}")
        return

    print("Starting benchmark (100 iterations)...")
    latencies = []
    with torch.inference_mode():
        for i in range(100):
            start = time.perf_counter()
            policy.select_action(observation)
            if device == "cuda":
                torch.cuda.synchronize()
            end = time.perf_counter()
            latencies.append((end - start) * 1000)  # ms

    avg_lat = np.mean(latencies)
    max_lat = np.max(latencies)
    min_lat = np.min(latencies)
    fps = 1000.0 / avg_lat

    print("\n--- Benchmark Results ---")
    print(f"Average Latency: {avg_lat:.2f} ms")
    print(f"Min Latency:     {min_lat:.2f} ms")
    print(f"Max Latency:     {max_lat:.2f} ms")
    print(f"Throughput:      {fps:.2f} FPS")


if __name__ == "__main__":
    benchmark()
