import os

env_file = ".env"
new_model = "gemini-2.0-flash-lite"

if os.path.exists(env_file):
    with open(env_file, "r") as f:
        lines = f.readlines()
    
    new_lines = []
    found = False
    for line in lines:
        if line.strip().startswith("GEMINI_MODEL="):
            new_lines.append(f"GEMINI_MODEL={new_model}\n")
            found = True
        else:
            new_lines.append(line)
    
    if not found:
        new_lines.append(f"\nGEMINI_MODEL={new_model}\n")
        
    with open(env_file, "w") as f:
        f.writelines(new_lines)
    
    print(f"✅ Updated {env_file} to use GEMINI_MODEL={new_model}")
else:
    print(f"❌ {env_file} not found")
