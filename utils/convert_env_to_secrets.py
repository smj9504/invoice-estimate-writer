import os

# 변환 대상 파일
ENV_FILE = ".env"
SECRETS_FILE = ".streamlit/secrets.toml"

# .env 파싱 함수
def parse_env_line(line):
    line = line.strip()
    if not line or line.startswith("#") or "=" not in line:
        return None
    key, value = line.split("=", 1)
    return key.strip(), value.strip().strip('"').strip("'")

# .env → .toml 변환 실행
def convert_env_to_toml(env_path, toml_path):
    if not os.path.exists(env_path):
        print(f" {env_path} 파일이 존재하지 않습니다.")
        return

    os.makedirs(os.path.dirname(toml_path), exist_ok=True)

    with open(env_path, "r", encoding="utf-8") as env_file:
        lines = env_file.readlines()

    secrets = {}
    for line in lines:
        parsed = parse_env_line(line)
        if parsed:
            key, value = parsed
            secrets[key] = value

    with open(toml_path, "w", encoding="utf-8") as secrets_file:
        for key, value in secrets.items():
            secrets_file.write(f'{key} = "{value}"\n')

    print(f"변환 완료: {toml_path}")

# 실행
if __name__ == "__main__":
    convert_env_to_toml(ENV_FILE, SECRETS_FILE)
